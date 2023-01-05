from pyncm import apis
import os
import requests
import wget
import eyed3
from eyed3.id3.frames import ImageFrame
import time
import re
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

REMOVE_ORIGINAL=False
#普通
#GLOBE_LEVEL = "standard"
#rate="128k"
#较高 （推荐）
GLOBE_LEVEL = "exhigh"
rate="320k"
#极高
#GLOBE_LEVEL = "lossless"
#rate="320k"
#无损 may need login or vip<<不建议,此种情况下音频码率已经超过了MP3协议的最高限制，所以会被压缩到320k,而且本人认为只要您不是什么世界级音乐家,也听不出来跟普通音质的区别
#过度追求高bit rate是会过犹不及的，因为这样会导致音频文件过大，而且音质也不会有太大的提升
#讲个笑话,之前假期我有个补课班的哥们,当时补课班的网也不是特别好,但他看视频坚持开1080P高码率结果卡成狗.我问他为啥不把画质调低点,他说因为他开了大会员,得好好享受下.但是我看他那个小手机的屏幕,最多分辨率也就720P(doge)
#GLOBE_LEVEL = " hires"
#rate="320k"


#login区，不想登录的话就用第一行，想的话参照 https://github.com/mos9527/pyncm/blob/master/pyncm/apis/login.py 改
#不用次次都运行，运行第一次之后注释掉就好
apis.login.LoginViaAnonymousAccount()

def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]" # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title) # 替换为下划线
    return new_title


def chackFFMPEG():
    if os.system("ffmpeg -version") != 0:
        print(Back.RED +"Error: ", "ffmpeg not found，装个ffmpeg呗~~~")
        exit(1)

def getArtistsString(artists):
    artistsString = ""
    for artist in artists:
        artistsString += artist["name"] + "/"
    return artistsString[:-1]

def toMp3(file_path):
    if file_path.endswith(".flac"):
        os.system("ffmpeg -i " + '"' + file_path + '"' +" -ab "+rate+" -f mp3 -acodec libmp3lame -y " + '"' + file_path[:-5] + '"' + ".mp3")
        if REMOVE_ORIGINAL:
            os.remove(file_path)
        return file_path[:-5] + ".mp3"
    else:
        return file_path

def rename(song_id,file_path,detail_object):
    file_path = toMp3(file_path)
    audiofile = eyed3.load(file_path)
    if (audiofile.tag == None):
        audiofile.initTag()
    if detail_object["code"] != 200:
        print(Back.RED +"Error: ", "你大概是没登陆或者缺少钞能力")
        return
    song_obj = detail_object["songs"][0]
    title=song_obj["name"]
    artists=getArtistsString(song_obj["ar"])
    album=song_obj["al"]["name"]
    if not os.path.exists('./img_cache/'+str(song_id)+'_cover.jpg'):
        wget.download(song_obj["al"]["picUrl"], out='./img_cache/'+str(song_id)+'_cover.jpg')
    tupTime=time.localtime(song_obj['publishTime']/1000)
    dateToTag=time.strftime("%Y-%m-%d", tupTime)
    print(Back.GREEN +"写入metadata成功" ,title,artists,album,dateToTag,"\n"*2)
    audiofile.tag.title = title
    audiofile.tag.artist = artists
    audiofile.tag.album = album
    audiofile.tag.release_date = dateToTag
    audiofile.tag.images.set(ImageFrame.FRONT_COVER, open('./img_cache/'+str(song_id)+'_cover.jpg','rb').read(), 'image/jpeg')
    audiofile.tag.save(version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')

def down(song_id,foder_name):
    results=apis.track.GetTrackAudioV1([song_id], level=GLOBE_LEVEL ,encodeType="flac")
    if results["data"][0]["code"] != 200:
        print(Back.RED +"Error: ", "你大概是没登陆或者缺少钞能力")
        return
    for result in results["data"]:
        print(Back.GREEN +"Downloading" , "id:",result["id"], result["size"]/(1000000), "MB", "MD5", result["md5"],"\n")
        detail = apis.track.GetTrackDetail([result["id"]],) #获取歌曲信息
        file_name = validateTitle(detail["songs"][0]["name"]) #detail里面的 alia 里面应该是歌曲的别名，但网易云或者用户可能没按协议办事，故在此忽略不做处理（谁家歌曲别名叫'2008年11月21日实况录音'）
        wget.download(result["url"], out=os.path.join(".",foder_name,file_name+".flac"))
        rename(result["id"] ,os.path.join(".",foder_name,file_name+".flac"),detail)

def main(type,id):
#    if type == "a":
#        os.mkdir("./a-"+str(id))
#        ablun = apis.album.GetAlbumDetailV1(id, level=GLOBE_LEVEL)
#        for song in ablun["songs"]:
#            down(song["id"],song["name"],"a-"+str(id))
#    elif type == "p":
    if type == "p":
        playlist = apis.playlist.GetPlaylistInfo(id,)
        if playlist["code"] != 200:
            print(Back.RED +"Error: ", "你大概是没登陆，登录以查看私有歌单（默认的喜欢也算）")
            return
        folderTitle = validateTitle(playlist["playlist"]["name"])
        try:
            os.mkdir("./"+folderTitle)
        except:
            print(Back.RED +"Error: ", "folder exist（已经好像下载过了呢）")
            exit(1)
        for song in playlist["playlist"]["trackIds"]:
            down(song["id"],folderTitle)
    else:
        print(Back.RED +"Error: ", "type error")#暂时木的用

if __name__ == "__main__":
    #main(input("a: ablun;p:playlist \n"),input("id:"))
    main("p", input("song list id:"))