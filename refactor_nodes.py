import os
import glob
import re

nodes_dir = os.path.join('apps', 'api', 'agent', 'nodes')
files = glob.glob(os.path.join(nodes_dir, '*.py'))

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    if 'ChatGoogleGenerativeAI' in content:
        content = re.sub(r'from langchain_google_genai import ChatGoogleGenerativeAI\n?', 'from agent.llm import get_llm\n', content)
        content = re.sub(r'ChatGoogleGenerativeAI\(model=[\"\']gemini-2\.0-flash[\"\'], temperature=([0-9.]+)\)', r'get_llm(temperature=\1)', content)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
            
print('Updated all nodes to use get_llm.')
