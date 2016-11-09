#-*-coding:utf-8-*- 
import sublime,sublime_plugin
import os,platform,re,logging,subprocess,json,sys,traceback,time
import uuid,urllib.parse,urllib.request,json,urllib.parse

curDir = os.path.dirname(os.path.realpath(__file__))

def plugin_loaded():
    global settings
    settings = {}
    settings = sublime.load_settings("APICloudWifiSync.sublime-settings")
    print("settings loaded!")
    print(settings.get("envlang"))

logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')

wifi_config_file=''
if 'windows' in platform.system().lower():
    wifi_config_file=os.path.join('c:\\','APICloud','workspace','config_info')
else:
    wifi_config_file=os.path.join(curDir,'tools','config_info')
logging.info('wifi_config_file is '+wifi_config_file)
############################################global function############################
def get_settings():
    return sublime.load_settings("wifi-sync.sublime-settings")

def is_service_start():
    if not os.path.exists(wifi_config_file):
        return False
    try:
        with open(wifi_config_file) as f:
            config=json.load(f)
            ip=config["ip"]
            websocket_port=config["websocket_port"]
    except:
        return False
    return True

def changeWorkspace(curDir,http_port):
    ''' change workspace '''
    rootDir = os.path.abspath(curDir).split(os.path.sep)[0]+os.path.sep
    if curDir == rootDir:
        return -1
    upperDir=os.path.dirname(curDir)
    workspaceEncoded='"'+urllib.parse.quote(upperDir)+'"'
    changeSpaceUrl='http://127.0.0.1:'+http_port+'?action=workspace&path='+workspaceEncoded
    logging.info('ChangeWorkspaceCommand url : '+ changeSpaceUrl)
    response = urllib.request.urlopen(changeSpaceUrl)
    html = response.read()
    time.sleep(0.2)

def isWidgetPath(path):
    isFound = False
    appFileList=os.listdir(path)
    if 'config.xml' in appFileList and 'index.html' in appFileList:
        with open(os.path.join(path,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)
            if len(searchResList)>0:
                isFound = True
    return isFound

def getWidgetPath(path):
    rootDir = os.path.abspath(path).split(os.path.sep)[0]+os.path.sep
    dirList = []
    for x in range(0,10):
        path = os.path.dirname(path)
        dirList.append(path)
        if path == rootDir:
            break

    syncPath=''
    for path in dirList:
        if isWidgetPath(path):
            syncPath = path
            break
    return syncPath

def getWifiInfo():
    time.sleep(4)
    if not os.path.exists(wifi_config_file):
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Please start first a real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
        else:
            sublime.message_dialog(u'请先启动真机同步服务')
        return        
    try:
        with open(wifi_config_file) as f:
            config=json.load(f)
            websocket_port=config["websocket_port"]
            if 0==websocket_port:
                if settings.get("envlang") =='en':
                    sublime.message_dialog(u'Services start not complete, manually check the service port information later!')
                elif settings.get("envlang") =="fr":
                    sublime.message_dialog(u'Le demarrage des services n''est pas complet, vérifier manuellement les informations de port de service plus tard!')
                else:
                    sublime.message_dialog(u'服务启动未完成，稍后请手动查看服务端口信息！')
                return
            ip=config["ip"]
            ip_list=ip.split(',')
            if len(ip_list)==1:
                if settings.get("envlang") =='en':
                    info='Port: '+str(websocket_port)+'\nip:'+ip
                elif settings.get("envlang") =="fr":
                    info='Port: '+str(websocket_port)+'\nip:'+ip
                else:
                    info='端口: '+str(websocket_port)+'\nip:'+ip
            else:
                if settings.get("envlang") =='en':
                    info='Port: '+str(websocket_port)
                elif settings.get("envlang") =="fr":
                    info='Port: '+str(websocket_port)
                else:
                    info='端口: '+str(websocket_port)
                i=0
                for ip_info in ip_list:
                    info=info+'\nip'+str(i)+': '+ip_info
                    i=i+1
    except Exception as e:
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Please start first a real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
        else:
            sublime.message_dialog(u'请先启动真机同步服务')
        return
    sublime.message_dialog(info)

def getAppId(srcPath):
    appId=-1
    if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
        print('getAppId:file no exist or not a folder!')
        return appId
    appFileList=os.listdir(srcPath)
    if 'config.xml' not in appFileList:
        print('getAppId: please make sure sync the correct folder!')
        return -1
    with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
        fileContent=f.read()
        r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
        searchResList=r.findall(fileContent)  
    if len(searchResList)>0:
        appId=searchResList[0]
    return appId

############################################end global function############################

class ApicloudWifiSyncCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiSyncCommand"""    
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.info('begin wifi sync')
        appId=getAppId(dirs[0])
        logging.info('appId: '+appId)
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]

        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return
        syncUrl='http://127.0.0.1:'+http_port+'?action=sync&appid='+appId
        logging.info('syncUrl is: '+ syncUrl)
        response = urllib.request.urlopen(syncUrl)

class EnApicloudWifiSyncCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiSyncCommand"""    
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "en"

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.info('begin wifi sync')
        appId=getAppId(dirs[0])
        logging.info('appId: '+appId)
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]

        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return
        syncUrl='http://127.0.0.1:'+http_port+'?action=sync&appid='+appId
        logging.info('syncUrl is: '+ syncUrl)
        response = urllib.request.urlopen(syncUrl)

class FrApicloudWifiSyncCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiSyncCommand"""    
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "fr"

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.info('begin wifi sync')
        appId=getAppId(dirs[0])
        logging.info('appId: '+appId)
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]

        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return
        syncUrl='http://127.0.0.1:'+http_port+'?action=sync&appid='+appId
        logging.info('syncUrl is: '+ syncUrl)
        response = urllib.request.urlopen(syncUrl)

class ApicloudWifiSyncallCommand(sublime_plugin.WindowCommand):
    '''wifi-sync all api'''
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0  and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList = os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        appId=getAppId(dirs[0])
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
            
        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return            
        syncallUrl='http://127.0.0.1:'+http_port+'?action=syncall&appid='+appId
        logging.info('syncallUrl is: '+ syncallUrl)
        response = urllib.request.urlopen(syncallUrl)

class EnApicloudWifiSyncallCommand(sublime_plugin.WindowCommand):
    '''wifi-sync all api'''
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "en"

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList = os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        appId=getAppId(dirs[0])
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
            
        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return            
        syncallUrl='http://127.0.0.1:'+http_port+'?action=syncall&appid='+appId
        logging.info('syncallUrl is: '+ syncallUrl)
        response = urllib.request.urlopen(syncallUrl)

class FrApicloudWifiSyncallCommand(sublime_plugin.WindowCommand):
    '''wifi-sync all api'''
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "fr"

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList = os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        appId=getAppId(dirs[0])
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
            
        if -1==changeWorkspace(dirs[0],http_port):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Make sure that the widget folder is not placed in the root directory!')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le dossier du widget n''est pas placé dans le répertoire racine!')
            else:
                sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return            
        syncallUrl='http://127.0.0.1:'+http_port+'?action=syncall&appid='+appId
        logging.info('syncallUrl is: '+ syncallUrl)
        response = urllib.request.urlopen(syncallUrl)

class ApicloudWifiPreviewCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiPreviewCommand"""
    def run(self, files):
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
        
        fileEncoded=urllib.parse.quote(files[0])
        previewUrl='http://127.0.0.1:'+http_port+'?action=review&path='+'"'+fileEncoded+'"'
        logging.info('previewUrl is: '+ previewUrl)
        response = urllib.request.urlopen(previewUrl)

    def is_enabled(self, files):
        if len(files) > 0:
            if not is_service_start():
                return False
            else:
                return True
        else:
            return False

    def is_visible(self, files):
        return len(files) > 0 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr") 

class EnApicloudWifiPreviewCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiPreviewCommand"""
    def run(self, files):
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
        
        fileEncoded=urllib.parse.quote(files[0])
        previewUrl='http://127.0.0.1:'+http_port+'?action=review&path='+'"'+fileEncoded+'"'
        logging.info('previewUrl is: '+ previewUrl)
        response = urllib.request.urlopen(previewUrl)

    def is_enabled(self, files):
        if len(files) > 0:
            if not is_service_start():
                return False
            else:
                return True
        else:
            return False

    def is_visible(self, files):
        return len(files) > 0 and settings.get("envlang") == "en"

class FrApicloudWifiPreviewCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiPreviewCommand"""
    def run(self, files):
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
        
        fileEncoded=urllib.parse.quote(files[0])
        previewUrl='http://127.0.0.1:'+http_port+'?action=review&path='+'"'+fileEncoded+'"'
        logging.info('previewUrl is: '+ previewUrl)
        response = urllib.request.urlopen(previewUrl)

    def is_enabled(self, files):
        if len(files) > 0:
            if not is_service_start():
                return False
            else:
                return True
        else:
            return False

    def is_visible(self, files):
        return len(files) > 0 and settings.get("envlang") == "fr" 

##############################################################################################

def BeforeSystemRequests():
    '''
    the systeminfo uploads to api of ..
    '''
    def get_system_version():
        system_name = platform.system()
        if system_name == 'Windows' and os.name == 'nt':
            system_machine = platform.platform().split('-')[0] + platform.platform().split('-')[1]
        elif system_name == 'Darwin':
            system_machine = 'Mac-os'
        else:
            system_machine = system_name
        return system_machine

    def post(url,data):
        data = urllib.parse.urlencode({'info':data}).encode('utf-8')
        req = urllib.request.Request(url,data)
        urllib.request.urlopen(req)
        return
    def index():
        apiUrl = 'http://www.apicloud.com/setSublimeInfo'
        systemInfo = {
            "system": get_system_version(),
            "uuid": hex(uuid.getnode())
        }
        try:
            systemInfo = json.dumps(systemInfo) 
            post(apiUrl,systemInfo)
        except Exception as e:
            print('exception is :',e)
        finally:
            pass
    try:        
        index()
    except Exception as e:
        pass   

class InstallWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' install wifi-sync service '''
    def run(self, dirs):
        if 'windows' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd='"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')
        elif 'linux' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd="wine "+'"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')     

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False

class EnInstallWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' install wifi-sync service '''
    def run(self, dirs):
        if 'windows' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd='"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')
        elif 'linux' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd="wine "+'"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service - cmd: '+installSyncCmd)
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')     

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrInstallWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' install wifi-sync service '''
    def run(self, dirs):
        if 'windows' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd='"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')
        elif 'linux' in platform.system().lower():
            exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
            installSyncCmd="wine "+'"'+exeCmdFile+'" -install'
            os.system(installSyncCmd)
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Complete the installation of APICloud synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Veuillez completer dabord l''installation du service de synchronisation')
            else:
                sublime.message_dialog(u'完成安装APICloud真机同步服务')     

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False

class StartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' start wifi-sync service '''
    def run(self, dirs):
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            startSyncCmd='"'+exeCmdFile+'" -start'
        elif 'linux' in platform.system().lower(): 
            startSyncCmd="wine "+'"'+exeCmdFile+'" -start'   
        logging.info('StartWifysyncAppCommand cmd : '+ startSyncCmd)
        os.system(startSyncCmd)
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False

class EnStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' start wifi-sync service '''
    def run(self, dirs):
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            startSyncCmd='"'+exeCmdFile+'" -start'
        elif 'linux' in platform.system().lower(): 
            startSyncCmd="wine "+'"'+exeCmdFile+'" -start'   
        logging.info('StartWifysyncAppCommand cmd : '+ startSyncCmd)
        os.system(startSyncCmd)
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' start wifi-sync service '''
    def run(self, dirs):
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            startSyncCmd='"'+exeCmdFile+'" -start'
        elif 'linux' in platform.system().lower(): 
            startSyncCmd="wine "+'"'+exeCmdFile+'" -start'   
        logging.info('StartWifysyncAppCommand cmd : '+ startSyncCmd)
        os.system(startSyncCmd)
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False

class StopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            stopSyncCmd='"'+exeCmdFile+'" -stop'
        elif 'linux' in platform.system().lower():
            stopSyncCmd="wine "+'"'+exeCmdFile+'" -stop'    
        logging.info('StopWifysyncAppCommand cmd : '+ stopSyncCmd)
        os.system(stopSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False

class EnStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            stopSyncCmd='"'+exeCmdFile+'" -stop'
        elif 'linux' in platform.system().lower():
            stopSyncCmd="wine "+'"'+exeCmdFile+'" -stop'    
        logging.info('StopWifysyncAppCommand cmd : '+ stopSyncCmd)
        os.system(stopSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        if 'windows' in platform.system().lower():
            stopSyncCmd='"'+exeCmdFile+'" -stop'
        elif 'linux' in platform.system().lower():
            stopSyncCmd="wine "+'"'+exeCmdFile+'" -stop'    
        logging.info('StopWifysyncAppCommand cmd : '+ stopSyncCmd)
        os.system(stopSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False

class GetWifisyncInfoCommand(sublime_plugin.WindowCommand):
    ''' get wifi-sync ip and port '''
    def run(self, dirs):
        if not os.path.exists(wifi_config_file):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return        
        try:
            with open(wifi_config_file) as f:
                config=json.load(f)
                websocket_port=config["websocket_port"]
                ip=config["ip"]
                ip_list=ip.split(',')
                if len(ip_list)==1:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    else:
                        info='端口: '+str(websocket_port)+'\nip:'+ip
                #if len(ip_list)==1:
                #    info='端口: '+str(websocket_port)+'\nip:'+ip
                else:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)
                    else:
                        info='端口: '+str(websocket_port)
                    i=0
                    for ip_info in ip_list:
                        info=info+'\nip'+str(i)+': '+ip_info
                        i=i+1
        except Exception as e:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return
        sublime.message_dialog(info)

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        else:
            return True
                
    def is_visible(self, dirs):
        return len(dirs) == 1 and not settings.get("envlang") =='en' and not settings.get("envlang") =='fr'

class EnGetWifisyncInfoCommand(sublime_plugin.WindowCommand):
    ''' get wifi-sync ip and port '''
    def run(self, dirs):
        if not os.path.exists(wifi_config_file):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return        
        try:
            with open(wifi_config_file) as f:
                config=json.load(f)
                websocket_port=config["websocket_port"]
                ip=config["ip"]
                ip_list=ip.split(',')
                if len(ip_list)==1:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    else:
                        info='端口: '+str(websocket_port)+'\nip:'+ip
                #if len(ip_list)==1:
                #    info='端口: '+str(websocket_port)+'\nip:'+ip
                else:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)
                    else:
                        info='端口: '+str(websocket_port)
                    i=0
                    for ip_info in ip_list:
                        info=info+'\nip'+str(i)+': '+ip_info
                        i=i+1
        except Exception as e:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return
        sublime.message_dialog(info)

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        else:
            return True
                
    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") =='en'

class FrGetWifisyncInfoCommand(sublime_plugin.WindowCommand):
    ''' get wifi-sync ip and port '''
    def run(self, dirs):
        if not os.path.exists(wifi_config_file):
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return        
        try:
            with open(wifi_config_file) as f:
                config=json.load(f)
                websocket_port=config["websocket_port"]
                ip=config["ip"]
                ip_list=ip.split(',')
                if len(ip_list)==1:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)+'\nip:'+ip
                    else:
                        info='端口: '+str(websocket_port)+'\nip:'+ip
                #if len(ip_list)==1:
                #    info='端口: '+str(websocket_port)+'\nip:'+ip
                else:
                    if settings.get("envlang") =='en':
                        info='Port: '+str(websocket_port)
                    elif settings.get("envlang") =="fr":
                        info='Port: '+str(websocket_port)
                    else:
                        info='端口: '+str(websocket_port)
                    i=0
                    for ip_info in ip_list:
                        info=info+'\nip'+str(i)+': '+ip_info
                        i=i+1
        except Exception as e:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please start first a real device synchronization service')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'S''il vous plaît lancez dabord un service de synchronisation de terminal réel')
            else:
                sublime.message_dialog(u'请先启动真机同步服务')
            return
        sublime.message_dialog(info)

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        else:
            return True
                
    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") =='fr'

############################ mac ####################################

class MacStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' mac start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('MacStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False          

class EnMacStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' mac start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('MacStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrMacStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' mac start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('MacStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False

class MacStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False 

class EnMacStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrMacStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'linux' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False
############################ linux ####################################

class LinuxStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' Linux start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('linuxStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False          

class EnLinuxStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' linux start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('linuxStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrLinuxStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' linux start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'JRE environment is missing')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Environnement JRE inexistant')
            else:
                sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('linuxStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        sublime.message_dialog(u'---->'+iosSyncCmd)
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False

class LinuxStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif not settings.get("envlang") =='en' and not settings.get("envlang") =='fr':
            return True
        else:
            return False 

class EnLinuxStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif settings.get("envlang") =='en':
            return True
        else:
            return False

class FrLinuxStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Stop APICloud real device synchronization service')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Arret du service de synchronisation de terminal reel')
        else:
            sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower() or 'darwin' in platform.system().lower():
            return False
        elif settings.get("envlang") =='fr':
            return True
        else:
            return False


######################## keymap #######################################
class ApicloudWifiPreviewKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudWifiPreviewKeyCommand"""
    def run(self, edit):
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Starting real device Preview')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Demarrage de l''apercu du terminal reel')
        else:
            sublime.status_message(u'开始真机预览')
        file_name=self.view.file_name()
        if len(file_name) > 0:
            logging.info('preview path is '+file_name)
            try:
                preview = ApicloudWifiPreviewCommand('')
                syncPathList=[]
                syncPathList.append(file_name)
                preview.run(syncPathList)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                if settings.get("envlang") =='en':
                    sublime.message_dialog(u'Real device preview is abnormal')
                elif settings.get("envlang") =="fr":
                    sublime.message_dialog(u'L''apercu sur le terminal reel est anormal')
                else:
                    sublime.error_message(u'真机预览出现异常')
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Preview of real device complete')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Apercu du terminal: Chargement achevE')
            else:
                sublime.status_message(u'真机预览完成')
        else:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please make sure that the current file is in the correct directory')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le fichier actuel se trouve dans le bon répertoire')
            else:
                sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudWifiSyncKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudWifiSyncKeyCommand"""
    def run(self, edit):
        if settings.get("envlang") =='en':
            sublime.message_dialog(u'Start real device synchronization')
        elif settings.get("envlang") =="fr":
            sublime.message_dialog(u'Demarrer la synchronisation du terminal reel')
        else:
            sublime.status_message(u'开始真机同步')
        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.info('sync path is '+syncPath)
            try:
                wifisync = ApicloudWifiSyncCommand('')
                syncPathList=[]
                syncPathList.append(syncPath)
                wifisync.run(syncPathList)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                if settings.get("envlang") =='en':
                    sublime.message_dialog(u'Real device synchronization is abnormal')
                elif settings.get("envlang") =="fr":
                    sublime.message_dialog(u'La synchronisation du terminal reel est anormal')
                else:
                    sublime.error_message(u'真机同步出现异常')
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Synchronization of real device complete')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Synchronisation du terminal achevE')
            else:
                sublime.status_message(u'真机同步完成')
        else:
            if settings.get("envlang") =='en':
                sublime.message_dialog(u'Please make sure that the current file is in the correct directory')
            elif settings.get("envlang") =="fr":
                sublime.message_dialog(u'Assurez-vous que le fichier actuel se trouve dans le bon répertoire')
            else:
                sublime.error_message(u'请确保当前文件所在目录正确')
        return   
        
# BeforeSystemRequests()