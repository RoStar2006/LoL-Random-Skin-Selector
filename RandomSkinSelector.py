##Imports
#Python Imports
import customtkinter
import random
import threading as t

#League Imports
from lcu_driver import Connector

#Window Code - Basic Blocks 
root = customtkinter.CTk()
root.title('Random Champion Skin')
root.resizable(False, False)

root.rowconfigure(0,weight=1)
root.columnconfigure(0,weight=1)

frame = customtkinter.CTkFrame(root)
frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

#Global Variables
filterDefault = customtkinter.IntVar(master = root, value = 0)
skinSelected = False

##UI 
#Sets all the UI Elements
def cleanUI():
    for label in frame.winfo_children():
        label.destroy()

    label = customtkinter.CTkLabel(frame, text = 'LoL Skin Randomizer', padx=5, pady=5,)
    label.cget("font").configure(size=28)
    label.pack()
        
    excludeCheckbox = customtkinter.CTkCheckBox(frame, text = 'Exclude Default Skin', variable = filterDefault, checkbox_height=20, checkbox_width=20, border_width=2)
    excludeCheckbox.cget("font").configure(size=20)
    excludeCheckbox.pack()
    
##Random Section
#Random Skin Function
async def randomizeSkin(connection):
    global filterDefault
    global errorLabel
    
    label = customtkinter.CTkLabel(frame, text = '−−−−−−−−−−−−−−−−−−−−−−−−−−−−')
    label.pack()

    random.seed()
    #Gets Skins from Chosen Champion
    skinList = await connection.request('get', '/lol-champ-select/v1/skin-carousel-skins')
    #Converts Json into Json String
    skinListStr = await skinList.json()

    #If it wasn't successful, error will be printed.
    if(len(skinListStr) == 0):
        errorLabel = customtkinter.CTkLabel(frame, text ='Error: Not in Champion Select or Champion Not Chosen!', text_color="red")
        errorLabel.pack()
    else:

        #Variables for storage
        skinName = ""
        skinID = 0
        skinIDs = []
        ownedSkinNames = []
        defaultFiltered = False

        #Searches Json for Owned Skins and Sends IDs to List
        for x in skinListStr:
            for key, value in x.items():
                #If we want to filter out the Base Skin
                if(filterDefault.get() == 1 and defaultFiltered == False):
                    defaultFiltered = True
                    break
                else:
                    #Keeps current iteration ID of Skin
                    if(key == 'id'):
                        skinID = value

                    if(key == 'name'):
                        skinName = value

                    #Same as Above
                    if(key == 'ownership'):
                        for y, z in value.items():
                            if(y == 'owned'):
                                if(z == True):
                                    skinIDs.append(skinID)
                                    ownedSkinNames.append(skinName)

        ownedSkinsLabel = customtkinter.CTkLabel(frame, text ='Owned skin(s): ')
        ownedSkinsLabel.cget("font").configure(size=16)
        ownedSkinsBox = customtkinter.CTkTextbox(frame, fg_color="transparent", activate_scrollbars=False, border_width=1)
        i = 0
        for x in ownedSkinNames:
            if not i == len(ownedSkinNames):
                ownedSkinsBox.insert(index="0.0", text=str(x) + "\n")
            else:
                ownedSkinsBox.insert(index="0.0", text=str(x))
            i += 1
        ownedSkinsBox.configure(state="disabled")

        #Randomly Chooses a Skin
        randNum = random.randint(0, len(skinIDs) - 1)

        pickedSkinLabel = customtkinter.CTkLabel(frame, text = 'Selected Skin: ' + ownedSkinNames[randNum], text_color="green", wraplength=500)
        pickedSkinLabel.cget("font").configure(size=16)

        pickedSkinLabel.pack()
        ownedSkinsLabel.pack()
        ownedSkinsBox.pack()

        #Wrap data into Json format for posting
        data = {
            "selectedSkinId": skinIDs[randNum]
        }

        #Sends Data to League Client
        skinChange = await connection.request('patch', '/lol-champ-select/v1/session/my-selection', data=data)

#Auto Mode
class StayAliveConnector():
    #Connector for Class
    connector = Connector()
    
    #To Keep the Program from Locking, this is a separated from the program in a thread.
    thread = t.Thread(target = connector.start)
    thread.daemon = True
    
    #Entry for Class
    def start(self):
        self.thread.start()

    #For Starting LCU-Driver
    # @connector.ready
    # async def connect(connection):
        # connectionLabel = customtkinter.CTkLabel(frame, text ='Connection to League Client API Successful!')
        # connectionLabel.pack()
    
    #Listens for Champion Selection Creation and Deletion
    @connector.ws.register('/lol-champ-select/v1/session', event_types = ('CREATE', 'DELETE',))
    async def inChampSelect(connection, event):
        global skinSelected
        cleanUI()
        
        #Checks which Event Type was triggered. Delete for not in Champion Selection. Create for when in Champion Selection
        if(event.type == 'Delete'):
            # ncsLabel = customtkinter.CTkLabel(frame, text = 'Not In Champion Selection')
            # ncsLabel.pack()
            
            if(skinSelected == True):
                skinSelected = False
        else:
            label = customtkinter.CTkLabel(frame, text = '−−−−−−−−−−−−−−−−−−−−−−−−−−−−')
            label.pack()

            icsLabel = customtkinter.CTkLabel(frame, text = 'Waiting for Champion selection')
            icsLabel.cget("font").configure(size=18)
            icsLabel.pack()
    
    #Listens for when Summoner chooses Champion
    @connector.ws.register('/lol-champ-select/v1/current-champion', event_types = ('CREATE',))
    async def champSelected(connection, event):
        global skinSelected
        
        #Precautionary Check
        if(event.data != 404):
            if(skinSelected != True):
                cleanUI()
                skinSelected = True
                
                #Randomize
                await randomizeSkin(connection)

    #For Closing LCU-Driver
    @connector.close
    async def close(connection):
        cleanUI()
        disconnectionLabel = customtkinter.CTkLabel(frame, text ='Disconnected from League Client API!', text_color="red")   
        disconnectionLabel.pack()

##Starter
#Applying Starting UI
cleanUI()
sAConnector = StayAliveConnector()
sAConnector.start()

#Starts Code
root.mainloop()