from pyncm import apis
import os
import requests
import wget
import eyed3
from eyed3.id3.frames import ImageFrame
import time

REMOVE_ORIGINAL=True
#普通
#GLOBE_LEVEL = "standard"
#rate="95k"
#较高 （推荐）
GLOBE_LEVEL = "exhigh"
rate="159k"
#极高
#GLOBE_LEVEL = "lossless"
#rate="192k"
#无损 may need login or vip
#GLOBE_LEVEL = " hires"
#rate="320k"#<<不知道是多少（要不你送我vip啊~~~），所以按照MP3最高码率来算的

#login区，不想登录的话就用第一行，想的话参照 https://github.com/mos9527/pyncm/blob/master/pyncm/apis/login.py 改
#不用次次都运行，运行第一次之后注释掉就好
apis.login.LoginViaAnonymousAccount()

def chackFFMPEG():
    if os.system("ffmpeg -version") != 0:
        print("Error: ", "ffmpeg not found，装个ffmpeg呗~~~")
        exit(1)

def getArtistsString(artists):
    artistsString = ""
    for artist in artists:
        artistsString += artist["name"] + "/"
    return artistsString[:-1]

def toMp3(file_path):
    if file_path.endswith(".flac"):
        os.system("ffmpeg -i " + file_path + " -ab "+rate+" -f mp3 -acodec libmp3lame -y " + file_path[:-5] + ".mp3")
        if REMOVE_ORIGINAL:
            os.remove(file_path)
        return file_path[:-5] + ".mp3"
    else:
        return file_path

def rename(song_id,file_path):
    file_path = toMp3(file_path)
    audiofile = eyed3.load(file_path)
    if (audiofile.tag == None):
        audiofile.initTag()
    #开始获取详细歌曲信息
    detail = apis.track.GetTrackDetail([song_id],)
    if detail["code"] != 200:
        print("Error: ", "你大概是没登陆或者缺少钞能力")
        return
    song_obj = detail["songs"][0]
    title=song_obj["name"]
    artists=getArtistsString(song_obj["ar"])
    album=song_obj["al"]["name"]
    if not os.path.exists('./img_cache/'+str(song_id)+'_cover.jpg'):
        wget.download(song_obj["al"]["picUrl"], out='./img_cache/'+str(song_id)+'_cover.jpg')
    tupTime=time.localtime(song_obj['publishTime']/1000)
    dateToTag=time.strftime("%Y-%m-%d", tupTime)
    print(title,artists,album,dateToTag)
    audiofile.tag.title = title
    audiofile.tag.artist = artists
    audiofile.tag.album = album
    audiofile.tag.release_date = dateToTag
    audiofile.tag.images.set(ImageFrame.FRONT_COVER, open('./img_cache/'+str(song_id)+'_cover.jpg','rb').read(), 'image/jpeg')
    audiofile.tag.save(version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')

def down(song_id,file_name,foder_name):
    results=apis.track.GetTrackAudioV1([song_id], level=GLOBE_LEVEL ,encodeType="flac")
    if results["data"][0]["code"] != 200:
        print("Error: ", "你大概是没登陆或者缺少钞能力")
        return
    for result in results["data"]:
        print("Downloading" ,result["id"], result["size"]/(1000000), result["md5"],"\n")
        wget.download(result["url"], out=os.path.join(".",foder_name,file_name+".flac"))
        rename(result["id"] ,os.path.join(".",foder_name,file_name+".flac"))

def main(type,id):
#    if type == "a":
#        os.mkdir("./a-"+str(id))
#        ablun = apis.album.GetAlbumDetailV1(id, level=GLOBE_LEVEL)
#        for song in ablun["songs"]:
#            down(song["id"],song["name"],"a-"+str(id))
#    elif type == "p":
    if type == "p":
        try:
            os.mkdir("./p-"+str(id))
        except:
            pass
        playlist = apis.playlist.GetPlaylistInfo(id,)
        #print(playlist)
        for song in playlist["playlist"]["trackIds"]:
            #print(song)
            down(song["id"],str(song["id"]),"p-"+str(id))
    else:
        print("Error: ", "type error")#暂时木的用

if __name__ == "__main__":
    #main(input("a: ablun;p:playlist \n"),input("id:"))
    main("p", input("song list id:"))