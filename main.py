import asyncio
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

async def generate_yna_rss():
    target_url = "https://www.yna.co.kr/graphic/index?site=bread_crumb"
    output_rss_file = "feed.xml"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"[*] 페이지 접속: {target_url}")
        await page.goto(target_url, wait_until="domcontentloaded")
        
        items = await page.locator("li:has(a.tit-news)").all()
        print(f"[*] 수집 대상 항목: {len(items)}개")
        
        # --- RSS 2.0 XML 뼈대 구축 ---
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        
        ET.SubElement(channel, "title").text = "연합뉴스 그래픽 뉴스"
        ET.SubElement(channel, "link").text = target_url
        ET.SubElement(channel, "description").text = "연합뉴스 최신 그래픽 뉴스 피드"
        ET.SubElement(channel, "language").text = "ko-KR"
        ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        for item in items:
            # 1. 제목 및 날짜 추출
            title_el = item.locator("a.tit-news .title01")
            time_el = item.locator(".txt-time")
            
            raw_title = (await title_el.inner_text()).strip() if await title_el.count() > 0 else ""
            raw_time = (await time_el.inner_text()).strip() if await time_el.count() > 0 else ""
            
            # 포맷: 제목 [2026-09-10 15:14]
            formatted_title = f"{raw_title} [{raw_time}]" if raw_time else raw_title
            
            # 2. 링크 및 설명 추출 (.share-data 속성 활용)
            share_data = item.locator(".share-data")
            if await share_data.count() > 0:
                description = (await share_data.get_attribute("data-share-body") or "").strip()
                link = (await share_data.get_attribute("data-share-url") or "").strip()
            else:
                link = (await item.locator("a.tit-news").get_attribute("href") or "").strip()
                description = ""
                
            if not link:
                continue

            # 3. RSS <item> 생성
            rss_item = ET.SubElement(channel, "item")
            ET.SubElement(rss_item, "title").text = formatted_title
            ET.SubElement(rss_item, "link").text = link
            ET.SubElement(rss_item, "description").text = description
            
            # 고유 식별자(GUID) 지정
            guid = ET.SubElement(rss_item, "guid")
            guid.text = link
            guid.set("isPermaLink", "true")

        await browser.close()

        # XML 들여쓰기 포맷팅 및 파일 저장
        ET.indent(rss, space="  ", level=0)
        tree = ET.ElementTree(rss)
        tree.write(output_rss_file, encoding="utf-8", xml_declaration=True)
        print(f"[*] RSS 생성이 완료되었습니다: {output_rss_file}")

if __name__ == "__main__":
    asyncio.run(generate_yna_rss())
