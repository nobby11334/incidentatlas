"""Verify the static site works below the GitHub project path /incidentatlas/."""
import pathlib,re,json,urllib.parse
root=pathlib.Path(__file__).resolve().parents[1];dist=root/'dist';html=(dist/'index.html').read_text()
for value in re.findall(r'(?:src|href)=["\']([^"\']+)',html):
 if value.startswith(('https://','http://','#','mailto:')):continue
 assert not value.startswith('/'),f'Origin-relative asset breaks project Pages: {value}'
 path=urllib.parse.urlsplit(value).path
 if path and path not in ['./','.']:assert (dist/path).exists(),f'Missing asset: {value}'
assert 'https://nobby11334.github.io/incidentatlas/' in html
assert 'mixedflint1.chatgpt.site' not in (dist/'review.js').read_text()
assert 'https://nobby11334.github.io/incidentatlas/#incident=' in (dist/'review.js').read_text()
assert not (dist/'source-cache').exists()
assert (dist/'data.json').stat().st_size>1000
workflow=(root/'.github/workflows/pages.yml').read_text()
assert 'path: _site' in workflow and 'pages: write' in workflow and 'id-token: write' in workflow
assert 'branches: [main]' in workflow and 'workflow_dispatch:' in workflow
print('GitHub Pages project-path assets, correction links and deployment configuration verified.')
