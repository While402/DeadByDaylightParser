from pathlib import Path
from typing import List, Optional
import requests
import json
import base64
import sqlite3

class DBDCharacter:
    def __init__(self, characterId: str, name : str, slugUrl: str, role: str, difficulty: str, inclusion: str, description: str, releaseDate: str, imageBase64: str):
        self.characterId = characterId
        self.name = name
        self.slugUrl = slugUrl
        self.role = role
        self.difficulty = difficulty
        self.inclusion = inclusion
        self.description = description
        self.releaseDate = releaseDate
        self.imageBase64 = imageBase64
    
    def isKiller(self):
        return self.role == "killer"
    
    def isSurvivor(self):
        return self.role == "survivor"

class CharactersDatabase:
    def __init__(self, characters: Optional[List[DBDCharacter]] = []):
        self.characters = characters
        self.killersList = []
        self.survivorsList = []

        if characters != []:
            self.killersList = filter(lambda character: character.isKiller(), self.characters)
            self.survivorsList = filter(lambda character: character.isSurvivor(), self.characters)
    
    def get_killers(self):
        return self.killersList
    
    def get_survivors(self):
        return self.survivorsList
    
    def add_new_character(self, character: DBDCharacter):
        self.characters.append(character)
        
        if character.role == "killer":
            self.killersList.append(character)
        else:
            self.survivorsList.append(character)


class DBDParser:
    def __init__(self, pageDataUrl = "https://deadbydaylight.com/page-data/news/page-data.json"):
        self.pageDataUrl = pageDataUrl
        self.CharactersDatabase = CharactersDatabase()
    
    def getRequest(self, url, data = None, headers = None, proxies = None, returnJson = False):
        session = requests.Session()

        session.headers = headers
        session.proxies = proxies

        requestData = session.get(url, data = data)
        
        if returnJson:
            return requestData.json()
        else:
            return requestData
    
    def writeCharactersInDatabase(self, databaseFileName, datarows):
        con = sqlite3.connect(databaseFileName)
        cur = con.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS characters(characterId TEXT PRIMARY KEY, name TEXT, slugUrl TEXT, role TEXT, difficulty TEXT, inclusion TEXT, description TEXT, releaseDate TEXT, imageBase64 TEXT)")

        for data in datarows:
            cur.execute('INSERT INTO characters (characterId, name, slugUrl, role, difficulty, inclusion, description, releaseDate, imageBase64) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                data.characterId,
                data.name,
                data.slugUrl,
                data.role,
                data.difficulty,
                data.inclusion,
                data.description,
                data.releaseDate,
                data.imageBase64
            ))
        
        con.commit()
        con.close()

    def imageToBase64(self, photoBytes) -> str:
        return base64.b64encode(photoBytes).decode('utf-8')

    def parseCharacters(self):
        jsonData = self.getRequest(self.pageDataUrl, returnJson = True)

        dbdPostsData = jsonData["result"]["pageContext"]["postsData"]
        charactersJsonList = dbdPostsData["characters"]["edges"]

        # charactersObjectList = []

        for character in range(len(charactersJsonList)):
            characterData = charactersJsonList[character]["node"]

            # print(type(characterData["difficulty"]))

            characterObject = DBDCharacter(
                characterData["id"],
                characterData["title"],
                characterData["slug"],
                characterData["role"],
                characterData["difficulty"],
                characterData["inclusion"],
                "" if characterData["description"] == None else characterData["description"],
                characterData["releaseDate"],
                self.imageToBase64(self.getRequest(characterData["headshot"]["url"]).content)
            )

            self.CharactersDatabase.add_new_character(characterObject)
        
        return self.CharactersDatabase

z = DBDParser()

l = z.parseCharacters()
z.writeCharactersInDatabase("db.db", l.characters)