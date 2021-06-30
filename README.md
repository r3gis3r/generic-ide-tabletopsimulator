# generic-ide-tabletopsimulator
A generic IDE connector for Tabletop Simulator - using Python

# How to install
Currently no pip install.
You need to :
 * checkout the git repo
 * Install [Python](https://www.python.org/downloads/), [nodejs](https://nodejs.org/en/download/) and [yarn](https://classic.yarnpkg.com/en/docs/install/#windows-stable)
 * Create a virtualenv
 * While your virtualenv is active  
 ```
 cd generic-ide-tabletopsimulator
 pip install -r requirements.txt
 yarn install
 ```

# How to use it
## The server part
The server part is supposed to run whenever you want to work on a TTS project that talks to TabletopSimulator.   
You run the server by using (in your virtual env)
### No IDE / manual config
```
python -u server.py --output-dir=path_to_your_project/fromtts
```
 * **Be very careful with the path you put here**, the server will constantly erase and reload the content from this folder with what comes from TTS.
 * _(Note the -u to tell python to run unbuffered and get prints immediately)_
 * Tip : Use a fromtts subfolder in your code source project
 * Optionaly the script takes a --lib-dirs argument if you want to override where to search for requires/includes 

### With PyCharm :
Create an External tool item : 

 * In _File > Settings_
 * In section _Tools > External tools_
 * Create a new entry
   * Name : TTS Server
   * Group : Tabletop Simulator (typing something in this field will create the new group)
   * Description : Tabletop simulator IDE server
   * Program : 
        * windows : <path_to_your_virtualenv>\Scripts\python.exe
        * linux/macos : <path_to_your_virtualenv>/bin/python
  * Arguments: 
     ```
     -u <path_to_your_checkout>/generic-ide-tabletopsimulator/server.py 
    --output-dir "<path_to_your_project>\fromtts"
    ```
  * _Synchronize files after exec_ : False
  * _Open console for tool output_ : True
  * _Make console active on stdout_ : True
  * _Make console active on stdout_ : False
  * _Ouput filter_ : `$FILE_PATH$:$LINE$:.*`   

In addition to that, we advise to create a shortcut for that in your toolbar
since you'll have to launch it each time you start working on your project

 * In _File > Settings_
 * _Appearance & Behavior > Menu & Toolbars_
 * _Navigation bar toolbar_
 * Press add, and search inside External tools, Tabletop Simulator section the TTS Server.

## The actions part
Actions are scripts that will request various things to TTS embedded server, 
results of these actions will be collected by the IDE server started in the previous step.

### Pull action
#### No IDE / Manual config
The command looks like that :
```
python command.py --output-dir path_to_your_project/fromtts --command pull
```
#### Pycharm config sample :
You'll create again an external tool as made in the server step.   
This time configuration should be :
   * Name : TTS Pull
   * Group : Tabletop Simulator (typing something in this field will create the new group)
   * Description : Tabletop simulator Pull Files
   * Program : 
        * windows : <path_to_your_virtualenv>\Scripts\python.exe
        * linux/macos : <path_to_your_virtualenv>/bin/python
  * Arguments: 
     ```
     <path_to_your_checkout>/generic-ide-tabletopsimulator/command.py 
    --output-dir "<path_to_your_project>\fromtts"
    --command pull
    ```
  * _Synchronize files after exec_ : **True**
  * _Open console for tool output_ : **False**
  * _Make console active on stdout_ : False
  * _Make console active on stdout_ : False
  * _Ouput filter_ : leave empty
    
For this one, we advise you to bind a keymap.
 * In _File > Settings_
 *  _Keymap_
 * find the _External tool_ / _Tabletop Simulator_ folder 
 * open it until you get the added items, and right click + add keyboard shortcut.
 * If you are used to Atom plugin, just use Ctrl+Shift+L

### Push action
#### No IDE / Manual config
The command looks like that :
```
python command.py --output-dir path_to_your_project/fromtts --command push
```
#### Pycharm config
Same as for pull, but replace `pull` with `push` in the command line

### Snippet exec
This allows you to run lua files directly on TTS without having any object nor modifying objects scripts.

#### No IDE / Manual config
The command looks like that :
```
python lua_snippet_runner.py --output-dir path_to_your_project/fromtts --file <filepath>
```

#### Pycharm config
Same as above to create a new entry. We take benefit of the Pycharm macro to pass the file path automatically for the one open.

   * Name : TTS Run snippet
   * Group : Tabletop Simulator (typing something in this field will create the new group)
   * Description : Tabletop simulator Run current file
   * Program : 
        * windows : <path_to_your_virtualenv>\Scripts\python.exe
        * linux/macos : <path_to_your_virtualenv>/bin/python
  * Arguments: 
     ```
     -u <path_to_your_checkout>/generic-ide-tabletopsimulator/lua_snippet_runner.py 
    --output-dir "<path_to_your_project>\fromtts"
    --file $FilePath$
    ```
  * _Synchronize files after exec_ : False
  * _Open console for tool output_ : **False**
  * _Make console active on stdout_ : False
  * _Make console active on stdout_ : False
  * _Ouput filter_ : leave empty
    

