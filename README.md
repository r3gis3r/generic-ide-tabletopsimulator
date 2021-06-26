# generic-ide-tabletopsimulator
A generic IDE connector for Tabletop Simulator - using Python

# How to install
Currently no pip install.
You need to :
 * checkout the git repo
 * Install python and yarn
 * Create a virtualenv
 * Inside the virutalenv 
 ```
 pip install -r requirements.txt
 ```

# How to use it
## The server part
 * The server part is supposed to run whenever you want to work on a TTS project that talks to TabletopSimulator
 * You run the server by using (in your virtual env)
 
```
python server.py --output-dir=path_to_your_project/fromtts
```
 * Be very careful with the path you put here, the server will constantly erase and reload the content from this folder with what comes from TTS.
 * Tip : Use a fromtts subfolder in your code source project

## The actions part
  * The integration will include a cli script that you can integrate with most ide as an external tool.
  Let's say for example you are using Pycharm or Intelij :
      * Go in _File > Settings_
      * In section _Tools > External tools_
      * Press add and fill the popup with relevant data to point to the (future) python script with correct argument using your virtualenv
      * you'll probably have to repeat that twice, once for _Push to TabletopSimulator_ and one for _Pull from TabletopSimulator_
      * Once done, you can go in the section _Keymap_ and find the _External tool_ folder, open it until you get the added items, and right click + add keyboard shortcut
      * Optionally you can also add a button in _Apparence & Behavior > Menus > Main toolbar_
