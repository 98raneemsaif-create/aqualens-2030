"""Explicit Developer API diagnostic. Never serialize keys or SDK exceptions."""
import json
import os
from pathlib import Path
from google import genai

output = Path('docs/evidence/phase_d/gemini_diagnostic.json')
if output.exists():
    raise RuntimeError('Use a new diagnostic evidence path rather than overwrite')
state = {name + '_present': bool(os.environ.get(name)) for name in (
    'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GENAI_USE_VERTEXAI',
    'GOOGLE_GENAI_USE_ENTERPRISE', 'GOOGLE_GEMINI_BASE_URL', 'GOOGLE_VERTEX_BASE_URL')}
for name in ('GOOGLE_GENAI_USE_VERTEXAI','GOOGLE_GENAI_USE_ENTERPRISE'):
    state[name + '_enabled'] = os.environ.get(name,'').lower() == 'true'
print(json.dumps(state),flush=True)
# Process-local overrides only: force the explicit Developer API path.
for name in ('GOOGLE_API_KEY','GOOGLE_GENAI_USE_VERTEXAI','GOOGLE_GENAI_USE_ENTERPRISE',
             'GOOGLE_GEMINI_BASE_URL','GOOGLE_VERTEX_BASE_URL'):
    os.environ.pop(name,None)
result = dict(environment=state,client='genai.Client(api_key=os.environ["GEMINI_API_KEY"])',tests=[])
def safe_error(error):
    code = getattr(error,'code',None)
    return dict(success=False,http_status=code if isinstance(code,int) else None,error_class=type(error).__name__)
try:
    with genai.Client(api_key=os.environ['GEMINI_API_KEY']) as client:
        try:
            models = list(client.models.list())
            names = [m.name for m in models if m.name and 'gemini' in m.name and 'generateContent' in (m.supported_actions or [])]
            result['models'] = dict(success=True,gemini_2_5_flash_listed='models/gemini-2.5-flash' in names,
                gemini_3_5_flash_listed='models/gemini-3.5-flash' in names,relevant_ids=names[:15])
        except Exception as error:
            result['models'] = safe_error(error)
        for model in ['gemini-2.5-flash','gemini-3.5-flash']:
            try:
                response = client.models.generate_content(model=model,contents='Reply with exactly: OK')
                test=dict(model=model,success=True,http_status=200,response_is_ok=(response.text or '').strip()=='OK')
            except Exception as error:
                test=dict(model=model,**safe_error(error))
            result['tests'].append(test)
            print(json.dumps(test),flush=True)
            if test['success']:
                result['selected_model']=model
                break
            if model=='gemini-2.5-flash' and test['http_status'] != 404:
                break
finally:
    output.write_text(json.dumps(result,indent=2)+'\n')
if not result.get('selected_model'):
    raise SystemExit(1)
