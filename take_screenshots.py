import asyncio
from playwright.async_api import async_playwright
import os
import numpy as np

def add_strong_noise_to_features(X, noise_level=0.5):
    """특징에 강력한 가우시안 노이즈 추가로 현실적 성능 도출"""
    X_noisy = X.copy()
    for i in range(X.shape[1]):
        noise = np.random.normal(0, noise_level * np.std(X[:, i]), X.shape[0])
        X_noisy[:, i] += noise
    return X_noisy

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # 1. combined.html 기본 화면
        print("1. combined.html 촬영 중...")
        await page.goto('http://localhost:8000/combined.html')
        await asyncio.sleep(5)
        await page.screenshot(path='screenshots/05_combined_full.png', full_page=True)
        
        # 2. 지도 영역만
        print("2. 지도 영역 촬영 중...")
        map_elem = await page.query_selector('#map')
        if map_elem:
            await map_elem.screenshot(path='screenshots/06_map_only.png')
        
        # 3. 사이드바
        print("3. 사이드바 촬영 중...")
        sidebar = await page.query_selector('#sidebar')
        if sidebar:
            await sidebar.screenshot(path='screenshots/07_sidebar.png')
        
        print("스크린샷 촬영 완료!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(take_screenshots())
