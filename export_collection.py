#!/usr/bin/env python3
"""
Export HighWire A4D Pipeline - QA API Collection as Postman Collection v2.1 JSON
"""
import json
import os
import uuid

BASE = r"D:\postman\.postman\postman\collections\HighWire A4D Pipeline - QA API Collection"
COLLECTION_ID = "270fECA46F9EcCaE14CaAA0A"
COLLECTION_NAME = "HighWire A4D Pipeline - QA API Collection"
OUTPUT = r"D:\postman\.postman\HighWire A4D Pipeline - QA API Collection.postman_collection.json"

def make_id():
    return str(uuid.uuid4())

def parse_yaml_file(filepath):
    """Simple YAML parser for our known schema using PyYAML if available, else manual."""
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        pass
    # Manual fallback - read the file and parse key lines
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return manual_yaml_parse(content)

def manual_yaml_parse(content):
    """Very basic YAML parser for our specific schema."""
    lines = content.split('\n')
    result = {}
    i = 0
    
    def get_indent(line):
        return len(line) - len(line.lstrip())
    
    def parse_value(val):
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        if val == 'true': return True
        if val == 'false': return False
        try: return int(val)
        except: pass
        return val
    
    # We'll use a stack-based approach
    stack = [{'obj': result, 'indent': -1}]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith('#'):
            i += 1
            continue
        
        indent = get_indent(stripped)
        
        # Pop stack to find parent
        while len(stack) > 1 and stack[-1]['indent'] >= indent:
            stack.pop()
        
        parent = stack[-1]['obj']
        
        # Check for list item
        if stripped.lstrip().startswith('- '):
            content_part = stripped.lstrip()[2:]
            if isinstance(parent, list):
                if ':' in content_part:
                    # dict item
                    new_dict = {}
                    parent.append(new_dict)
                    colon_idx = content_part.index(':')
                    k = content_part[:colon_idx].strip()
                    v = content_part[colon_idx+1:].strip()
                    if v:
                        new_dict[k] = parse_value(v)
                    else:
                        new_dict[k] = None
                    stack.append({'obj': new_dict, 'indent': indent + 2})
                else:
                    parent.append(parse_value(content_part))
            i += 1
            continue
        
        # Key: value
        if ':' in stripped.lstrip():
            rest = stripped.lstrip()
            colon_idx = rest.index(':')
            k = rest[:colon_idx].strip()
            v = rest[colon_idx+1:].strip()
            
            if v == '|-' or v == '|':
                # Block scalar - collect lines
                block_lines = []
                base_indent = None
                i += 1
                while i < len(lines):
                    bl = lines[i]
                    if not bl.strip():
                        block_lines.append('')
                        i += 1
                        continue
                    bl_indent = get_indent(bl)
                    if base_indent is None:
                        base_indent = bl_indent
                    if bl_indent < base_indent and bl.strip():
                        break
                    block_lines.append(bl[base_indent:] if base_indent else bl)
                    i += 1
                # Remove trailing empty lines for |-
                while block_lines and not block_lines[-1]:
                    block_lines.pop()
                parent[k] = '\n'.join(block_lines)
                continue
            elif v == '':
                # Could be a nested object or list - peek next line
                if i + 1 < len(lines):
                    next_line = lines[i+1]
                    next_stripped = next_line.lstrip()
                    if next_stripped.startswith('- '):
                        new_list = []
                        parent[k] = new_list
                        stack.append({'obj': new_list, 'indent': indent + 2})
                    else:
                        new_dict = {}
                        parent[k] = new_dict
                        stack.append({'obj': new_dict, 'indent': indent + 2})
                else:
                    parent[k] = None
            else:
                parent[k] = parse_value(v)
        
        i += 1
    
    return result

def build_url(raw_url):
    """Build Postman v2.1 URL object from raw URL string."""
    return {
        "raw": raw_url,
        "host": [raw_url]
    }

def build_auth(auth_data):
    """Build Postman v2.1 auth object."""
    if not auth_data:
        return None
    auth_type = auth_data.get('type', '')
    if auth_type == 'basic':
        creds = auth_data.get('credentials', {})
        return {
            "type": "basic",
            "basic": [
                {"key": "username", "value": creds.get('username', ''), "type": "string"},
                {"key": "password", "value": creds.get('password', ''), "type": "string"}
            ]
        }
    return None

def build_headers(headers_data):
    """Build Postman v2.1 headers array."""
    if not headers_data:
        return []
    if isinstance(headers_data, dict):
        return [{"key": k, "value": v} for k, v in headers_data.items()]
    if isinstance(headers_data, list):
        result = []
        for h in headers_data:
            if isinstance(h, dict):
                item = {"key": h.get('key', ''), "value": h.get('value', '')}
                if h.get('disabled'):
                    item['disabled'] = True
                result.append(item)
        return result
    return []

def build_body(body_data):
    """Build Postman v2.1 body object."""
    if not body_data:
        return None
    btype = body_data.get('type', '')
    content = body_data.get('content', '')
    
    if btype == 'json':
        return {
            "mode": "raw",
            "raw": content if isinstance(content, str) else json.dumps(content),
            "options": {"raw": {"language": "json"}}
        }
    elif btype == 'text':
        return {
            "mode": "raw",
            "raw": content if isinstance(content, str) else str(content),
            "options": {"raw": {"language": "text"}}
        }
    elif btype == 'xml':
        return {
            "mode": "raw",
            "raw": content if isinstance(content, str) else str(content),
            "options": {"raw": {"language": "xml"}}
        }
    elif btype == 'urlencoded':
        items = []
        if isinstance(content, dict):
            items = [{"key": k, "value": str(v), "type": "text"} for k, v in content.items()]
        elif isinstance(content, list):
            items = [{"key": i.get('key',''), "value": str(i.get('value','')), "type": "text"} for i in content]
        return {"mode": "urlencoded", "urlencoded": items}
    elif btype == 'formdata':
        items = []
        if isinstance(content, list):
            for item in content:
                fd_item = {
                    "key": item.get('key', ''),
                    "type": item.get('type', 'text')
                }
                if item.get('type') == 'file':
                    src = item.get('src', '')
                    if isinstance(src, list):
                        fd_item['src'] = src[0] if src else ''
                    else:
                        fd_item['src'] = src
                else:
                    fd_item['value'] = str(item.get('value', ''))
                if item.get('description'):
                    fd_item['description'] = item['description']
                items.append(fd_item)
        return {"mode": "formdata", "formdata": items}
    return None

def build_events(scripts_data):
    """Build Postman v2.1 event array from scripts."""
    if not scripts_data:
        return []
    events = []
    for s in scripts_data:
        stype = s.get('type', '')
        code = s.get('code', '')
        if isinstance(code, str):
            exec_lines = code.split('\n')
        else:
            exec_lines = [str(code)]
        
        if stype == 'afterResponse':
            listen = 'test'
        elif stype == 'beforeRequest':
            listen = 'prerequest'
        else:
            continue
        
        events.append({
            "listen": listen,
            "script": {
                "type": "text/javascript",
                "exec": exec_lines
            }
        })
    return events

def build_request_item(name, yaml_data):
    """Build a Postman v2.1 request item."""
    item = {
        "name": name,
        "_postman_id": make_id(),
        "request": {
            "method": yaml_data.get('method', 'GET'),
            "header": build_headers(yaml_data.get('headers')),
            "url": build_url(yaml_data.get('url', '')),
        },
        "response": []
    }
    
    # Description
    if yaml_data.get('description'):
        item['request']['description'] = yaml_data['description']
    
    # Body
    body = build_body(yaml_data.get('body'))
    if body:
        item['request']['body'] = body
    
    # Auth
    auth = build_auth(yaml_data.get('auth'))
    if auth:
        item['request']['auth'] = auth
    
    # Events (scripts)
    events = build_events(yaml_data.get('scripts'))
    if events:
        item['event'] = events
    
    return item

def load_folder(folder_path, folder_name):
    """Load all requests from a folder directory."""
    items = []
    
    # Get all .request.yaml files sorted by order
    request_files = []
    for fname in os.listdir(folder_path):
        if fname.endswith('.request.yaml'):
            fpath = os.path.join(folder_path, fname)
            yaml_data = parse_yaml_file(fpath)
            if yaml_data:
                req_name = fname.replace('.request.yaml', '')
                # Use name field if present
                if yaml_data.get('name'):
                    req_name = yaml_data['name']
                order = yaml_data.get('order', 9999999)
                request_files.append((order, req_name, yaml_data))
    
    request_files.sort(key=lambda x: x[0])
    
    for order, req_name, yaml_data in request_files:
        item = build_request_item(req_name, yaml_data)
        items.append(item)
    
    folder_item = {
        "name": folder_name,
        "_postman_id": make_id(),
        "item": items
    }
    return folder_item

# Load collection definition
def_path = os.path.join(BASE, '.resources', 'definition.yaml')
col_def = parse_yaml_file(def_path) if os.path.exists(def_path) else {}

# Build collection variables
variables = []
if col_def and col_def.get('variables'):
    vars_data = col_def['variables']
    if isinstance(vars_data, dict):
        for k, v in vars_data.items():
            variables.append({
                "key": k,
                "value": str(v) if v is not None else "",
                "type": "string"
            })
    elif isinstance(vars_data, list):
        for item in vars_data:
            variables.append({
                "key": item.get('key', ''),
                "value": str(item.get('value', '')) if item.get('value') is not None else "",
                "type": "string"
            })

# Load folders sorted by order
folders = []
for fname in os.listdir(BASE):
    fpath = os.path.join(BASE, fname)
    if os.path.isdir(fpath) and not fname.startswith('.'):
        # Check for folder definition
        folder_def_path = os.path.join(fpath, '.resources', 'definition.yaml')
        folder_order = 9999
        if os.path.exists(folder_def_path):
            folder_def = parse_yaml_file(folder_def_path)
            if folder_def:
                folder_order = folder_def.get('order', 9999)
        folders.append((folder_order, fname, fpath))

folders.sort(key=lambda x: x[0])

# Build collection items
collection_items = []
for order, folder_name, folder_path in folders:
    folder_item = load_folder(folder_path, folder_name)
    collection_items.append(folder_item)

# Build the full collection
collection = {
    "info": {
        "_postman_id": COLLECTION_ID,
        "name": COLLECTION_NAME,
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "_exporter_id": "58605332"
    },
    "item": collection_items,
    "variable": variables
}

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(collection, f, indent=2, ensure_ascii=False)

print(f"SUCCESS: Collection exported to {OUTPUT}")
print(f"Folders: {len(collection_items)}")
total_requests = sum(len(f['item']) for f in collection_items)
print(f"Total requests: {total_requests}")
print(f"Variables: {len(variables)}")
