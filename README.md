# generic-ide-tabletopsimulator
A generic IDE Connector for Tabletop Simulator - using Python

# Features
 * Pull files from TTS
 * Push files with save and reload to TTS
 * Print messages from TTS
 * Print errors with links to required files and code line.
 * Launch code snippet files on global or objects
 * :star2: Hot reload of a single object : **way faster**, without save&reload
 * :star2: Hot reload of modified objects only (WIP)

# How to install

You need to :
 * Checkout the git repo
 * Install [Python](https://www.python.org/downloads/) (3.8+), [nodejs](https://nodejs.org/en/download/) and [yarn](https://classic.yarnpkg.com/en/docs/install/#windows-stable)
 * _optional_ [Create a python virtualenv](https://docs.python.org/3/library/venv.html)
 * With your virtualenv is active  
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

### With IntelliJ / PyCharm :
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
  * _Open console for tool output_ : **True**
  * _Make console active on stdout_ : **True**
  * _Make console active on stdout_ : False
  * _Ouput filter_ : `$FILE_PATH$:$LINE$:.*`   

In addition to that, we advise to create a _shortcut_ for that in your toolbar
since you'll have to launch it each time you start working on your project

 * In _File > Settings_
 * _Appearance & Behavior > Menu & Toolbars_
 * _Navigation bar toolbar_
 * Press add, and search inside External tools, Tabletop Simulator section the TTS Server.


Also if you are using Windows, the default console encoding might be wrong.  
Go in _File > Settings_ and then _Editor > General > Console_ and make sure the default encoding is set to UTF-8

## The actions commands
Actions are scripts that will request various things to TTS embedded server, 
results of these actions will be collected by the IDE server started in the previous step.

### Pull action
#### No IDE / Manual config
The command looks like that :
```
python command.py --output-dir path_to_your_project/fromtts --command pull
```
#### IntelliJ / Pycharm config sample :
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

---

### Push action
#### No IDE / Manual config
The command looks like that :
```
python command.py --output-dir path_to_your_project/fromtts --command push
```
#### IntelliJ / Pycharm config
Same as for pull, but replace `pull` with `push` in the command line

---

### Snippet exec
This allows you to run lua files directly on TTS without having any object nor modifying objects scripts.

You can create your own snippet/scratches files and run them in the context of TTS.  
In order to make a script run in the context of one particular objects : 
 * Copy the object GUID from TTS
 * Add the following line in your lua snippet file :   
`-- FOR_GUID : 892585`   
   _where 892585 is the guid of the object you want to run the script for_
   
#### No IDE / Manual config
The command looks like that :
```
python lua_snippet_runner.py --output-dir path_to_your_project/fromtts --file <filepath>
```

#### IntelliJ / Pycharm config
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
    
---

### Hot reload one object

#### No IDE / Manual config
The command looks like that :
```
python object_patcher.py --output-dir path_to_your_project/fromtts --object <the_object_guid>
```

#### IntelliJ / Pycharm config
Here we advise to configure a run profile that is easier to modify.   
Just configure it to run the command of manual config above.

---
### Hot reload all updated objects

#### No IDE / Manual config
The command looks like that :
```
python command.py --output-dir path_to_your_project/fromtts --command soft_push
```

#### IntelliJ / Pycharm config
Same as push/pull advised

---

# Extra IntelliJ/Pycharm information
We strongly advise you to have a look to :
 * [IntelliJ-Luanalysis](https://github.com/Benjamin-Dobell/IntelliJ-Luanalysis)
 * [tts-types](https://github.com/Benjamin-Dobell/tts-types)

# Extra TTS Information
If you are working on TTS plugin, we strongly advise you to visit :  
[https://tts-community.github.io/](https://tts-community.github.io/)   
there is a lot of useful resources in this website and also other IDE integrations if this one doesn't fit your needs :)