import json
import os

def generate_docs():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    json_path = os.path.join(base_dir, 'simulation', 'data', 'results', 'comparison.json')
    
    with open(json_path, 'r') as f:
        kpis = json.load(f)
        
    templates = {
        'docs/templates/README.template.md': 'README.md',
        'docs/templates/SUBMISSION.template.md': 'docs/SUBMISSION.md'
    }
    
    for template_rel, output_rel in templates.items():
        template_path = os.path.join(base_dir, template_rel)
        output_path = os.path.join(base_dir, output_rel)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Format the content using the KPIs dictionary
        formatted_content = content.format(**kpis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
            
        print(f"Generated {output_rel} from {template_rel}")

if __name__ == "__main__":
    generate_docs()
