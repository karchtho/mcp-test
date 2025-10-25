#!/usr/bin/env python3
import asyncio
import json
import pymysql
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from config import DATABASE_CONFIG
import os

# Initialisation du serveur MCP
server = Server("cours-mcp")

# Connexion à la base de données
def get_db_connection():
    return pymysql.connect(
        host=DATABASE_CONFIG['host'],
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password'],
        database=DATABASE_CONFIG['database'],
        charset=DATABASE_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )

# Liste des outils disponibles
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="rechercher_cours",
            description="Recherche dans vos cours par mot-clé",
            inputSchema={
                "type": "object",
                "properties": {
                    "mot_cle": {
                        "type": "string",
                        "description": "Mot-clé à rechercher dans vos cours"
                    }
                },
                "required": ["mot_cle"]
            }
        ),
        Tool(
            name="ajouter_cours",
            description="Ajoute un nouveau cours ou exercice",
            inputSchema={
                "type": "object",
                "properties": {
                    "titre": {"type": "string", "description": "Titre du cours"},
                    "matiere": {"type": "string", "description": "Matière"},
                    "type_contenu": {"type": "string", "enum": ["cours", "exercice", "corrige"]},
                    "contenu": {"type": "string", "description": "Contenu du cours"}
                },
                "required": ["titre", "contenu"]
            }
        )
    ]

# Gestion des appels d'outils
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "rechercher_cours":
        mot_cle = arguments["mot_cle"]
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT * FROM cours 
                WHERE titre LIKE %s OR contenu LIKE %s OR matiere LIKE %s
                ORDER BY date_ajout DESC
                LIMIT 10
                """
                cursor.execute(sql, (f"%{mot_cle}%", f"%{mot_cle}%", f"%{mot_cle}%"))
                results = cursor.fetchall()
                
                if not results:
                    return [TextContent(type="text", text=f"Aucun cours trouvé pour '{mot_cle}'")]
                
                response = f"📚 **{len(results)} cours trouvé(s) pour '{mot_cle}':**\n\n"
                for cours in results:
                    response += f"**{cours['titre']}**\n"
                    response += f"Matière: {cours['matiere'] or 'Non définie'}\n"
                    response += f"Type: {cours['type_contenu']}\n"
                    response += f"Contenu: {cours['contenu'][:300]}...\n"
                    response += f"Ajouté le: {cours['date_ajout']}\n\n"
                
                return [TextContent(type="text", text=response)]
        finally:
            connection.close()
    
    elif name == "ajouter_cours":
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO cours (titre, matiere, type_contenu, contenu)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    arguments["titre"],
                    arguments.get("matiere"),
                    arguments.get("type_contenu", "cours"),
                    arguments["contenu"]
                ))
                connection.commit()
                return [TextContent(type="text", text=f"✅ Cours '{arguments['titre']}' ajouté avec succès !")]
        finally:
            connection.close()

if __name__ == "__main__":
    async def main():
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="cours-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    
    asyncio.run(main())