import requests
import re

url = 'https://www.instagram.com/p/DZ9xP_AyYAM/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

r_embed = requests.get(url.rstrip('/') + '/embed/captioned/', headers=headers)
matches = re.findall(r'https?://[^\s"\'\\]+(?:cdninstagram|fbcdn)[^\s"\'\\]+', r_embed.text)
print("CDN matches count:", len(matches))
for m in list(set(matches))[:8]:
    clean_m = m.replace('\\u0026', '&').replace('\\/', '/')
    print("Match:", clean_m[:150])

# Check caption in embed
caption_match = re.findall(r'class=\"Caption\"[^>]*>(.*?)</div>', r_embed.text, re.DOTALL)
if caption_match:
    print("Caption found raw:", caption_match[0][:200])
else:
    # Check window.__additionalDataLoaded or similar
    print("Caption div regex not found")
