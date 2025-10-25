#!/usr/bin/env python3
from flask import Flask, request, jsonify
import asyncio
import json
from server import handle_call_tool, handle_list_tools

app = Flask(__name__)

@app.route('/mcp/tools', methods=['GET'])
async def list_tools():
    tools = await handle_list_tools()
    return jsonify([{
        'name': tool.name,
        'description': tool.description,
        'inputSchema': tool.inputSchema
    } for tool in tools])

@app.route('/mcp/call', methods=['POST'])
async def call_tool():
    data = request.json
    tool_name = data.get('name')
    arguments = data.get('arguments', {})
    
    try:
        result = await handle_call_tool(tool_name, arguments)
        return jsonify({
            'success': True,
            'result': result[0].text if result else "Aucun résultat"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Serveur MCP HTTP actif'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)