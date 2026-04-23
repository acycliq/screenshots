import http.server
import json
import os
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).parent

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = self.get_mapped_data()
            self.wfile.write(json.dumps(data).encode())
        else:
            return super().do_GET()

    def get_mapped_data(self):
        folders = ['with_rho_g', 'without_rho_g']
        manifests = {}
        screenshots = {}
        
        # Load color scheme
        color_scheme = {}
        color_file = Path('/home/dimitris/Desktop/cell_colour_scheme_yao.json')
        if color_file.exists():
            with open(color_file, 'r') as f:
                raw_colors = json.load(f)
                # Normalize keys for easier matching
                for k, v in raw_colors.items():
                    # "0261 CA1-ProS Glut_1" -> "CA1-ProS Glut"
                    clean_k = ' '.join(k.split(' ')[1:]) # Remove ID
                    clean_k = clean_k.split('_')[0] # Remove trailing _1
                    color_scheme[clean_k] = v
                    # Also keep full key just in case
                    color_scheme[k] = v

        for folder in folders:
            folder_path = BASE_DIR / folder
            manifest_path = folder_path / 'manifest.json'
            
            # Load manifest
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifests[folder] = json.load(f)
            else:
                manifests[folder] = []

            # Load screenshots (sorted alphabetically to match sequential order)
            images = sorted([f.name for f in folder_path.glob('*.png')])
            screenshots[folder] = images

        # Create master list of unique names
        all_names = set()
        for m in manifests.values():
            for entry in m:
                all_names.add(entry['name'])
        
        # Sort names: first by 'with_rho_g' count if possible
        with_rho_counts = {e['name']: e['count'] for e in manifests['with_rho_g']}
        sorted_names = sorted(list(all_names), key=lambda x: with_rho_counts.get(x, 0), reverse=True)

        result = []
        for name in sorted_names:
            item = {'name': name, 'with': {}, 'without': {}, 'color': '#888888'}
            
            # Find color
            if name in color_scheme:
                item['color'] = color_scheme[name]
            else:
                # Try matching by removing the leading number "037 DG Glut" -> "DG Glut"
                parts = name.split(' ')
                if len(parts) > 1 and parts[0].isdigit():
                    clean_name = ' '.join(parts[1:])
                    if clean_name in color_scheme:
                        item['color'] = color_scheme[clean_name]

            # Map with_rho_g
            with_idx = next((i for i, e in enumerate(manifests['with_rho_g']) if e['name'] == name), -1)
            if with_idx != -1 and with_idx < len(screenshots['with_rho_g']):
                item['with'] = {
                    'count': manifests['with_rho_g'][with_idx]['count'],
                    'image': f"with_rho_g/{screenshots['with_rho_g'][with_idx]}"
                }
            else:
                item['with'] = {'count': 0, 'image': 'blank.png'}

            # Map without_rho_g
            without_idx = next((i for i, e in enumerate(manifests['without_rho_g']) if e['name'] == name), -1)
            if without_idx != -1 and without_idx < len(screenshots['without_rho_g']):
                item['without'] = {
                    'count': manifests['without_rho_g'][without_idx]['count'],
                    'image': f"without_rho_g/{screenshots['without_rho_g'][without_idx]}"
                }
            else:
                item['without'] = {'count': 0, 'image': 'blank.png'}
            
            result.append(item)
        
        return result

if __name__ == '__main__':
    print(f"Starting Zen Dashboard server at http://localhost:{PORT}")
    http.server.test(HandlerClass=DashboardHandler, port=PORT)
