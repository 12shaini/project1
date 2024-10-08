from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

#api key connection

def Api_connect():
    Api_Id="AIzaSyCggW6z0SfllsuOWWlbCnDych4SbR_SImg"

    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey=Api_Id)

    return youtube

youtube=Api_connect()

#get channels information
def get_channel_info(channel_id):
        request=youtube.channels().list(
                         part="snippet,ContentDetails,statistics",
                         id=channel_id
        )
        response=request.execute()

        for i in response['items']:
            data=dict(Channel_Name=i["snippet"]['title'],
                    Channel_Id=i["id"],
                    SubscriberCount=i['statistics']['subscriberCount'],
                    Views=i["statistics"]["viewCount"],
                    Total_videos=i["statistics"]["videoCount"],
                    Channal_Description=i["snippet"]["description"],
                    Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
        return data
        
 #get video ids
def get_videos_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id="UC00qEBA94D-vjRsvX6_EaVQ",
                                    part="contentDetails").execute()
    playlist_Id=response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    next_page_token=None

    while True:

        response1=youtube.playlistItems().list(
                                            part='snippet',
                                            playlistId=playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][0]['snippet']['resourceId']['videoId'])
        next_page_token=response1.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids

#get video information
def get_video_info(video_ids):
        Video_data=[]
        for video_id in video_ids:
                request=youtube.videos().list(
                        part="snippet,ContentDetails,statistics",
                        id=video_id                
                
                )
                response=request.execute()

                for item in response["items"]:
                    data=dict(channel_Name=item['snippet']['channelTitle'],
                            channel_Id=item['snippet']['channelId'],
                            video_id=item['id'],
                            Title=item['snippet']['title'],
                            Tags=item['snippet'].get('tags'),
                            Thumbnail=item['snippet']['thumbnails']['default']['url'],
                            Description=item['snippet'].get('description'),
                            published_Datee=item['snippet']['publishedAt'],
                            Duration=item['contentDetails']['duration'],
                            Views=item['statistics'].get('viewCount'),
                            Likes=item['statistics'].get('likeCount'),
                            Comments=item['statistics'].get('commentCount'),
                            Favorite_Count=item['statistics']['favoriteCount'],
                            Definition=item['contentDetails']['definition'],
                            Caption_Status=item['contentDetails']['caption'],
                            )
                    Video_data.append(data)
        return Video_data

#get comment information
def get_comment_info(video_ids):
    
    comment_data=[]
  
    for video_id in video_ids:
        request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
        response=request.execute()

        for item in response['items']:
            data=dict(comment_Id=item['snippet']['topLevelComment']['id'],
                        video_id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        comment_published=item['snippet']['topLevelComment']['snippet']['publishedAt'])
            
            comment_data.append(data)
  
    
    return  comment_data

#get_playlist_details

def get_playlist_details(channel_id):

        next_page_token=None
        All_data=[]
        while True:
                request=youtube.playlists().list(
                        part='snippet,contentDetails',
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token
                )
                response=request.execute()

                for item in response['items']:
                     data=dict(playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                publishedAt=item['snippet']['publishedAt'],
                                Video_Count=item['contentDetails']['itemCount'])
                     All_data.append(data)
                next_page_token=response.get('nextPageToken')

                if next_page_token is None:
                    break
        return  All_data

#upload to mongoDB

client=pymongo.MongoClient("mongodb+srv://dizosa2112:anthuvan@shalini.q1ctssh.mongodb.net/?retryWrites=true&w=majority&appName=shalini")
db=client["youtube_data"]

def Channel_details(channel_id):
    Ch_details=get_channel_info(channel_id)
    Pl_details=get_playlist_details(channel_id)
    Vi_ids=get_videos_ids(channel_id)
    Vi_details=get_video_info(Vi_ids)
    Com_details=get_comment_info(Vi_ids)

    coll1=db["Channel_details"]
    coll1.insert_one({"channel_information": Ch_details,"playlist_information":Pl_details,
                      "video_information":Vi_details,"comment_information":Com_details})
    return "upload completed successfully"


#Table creation for channels,playlists,videos,comments

def channels_table(channel_name_s):
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="anthuvan",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

   

    create_query='''create table if not exists channels(Channel_Name varchar(100),
                                                    Channel_Id varchar(80) primary key,
                                                    SubscriberCount bigint,
                                                    Views bigint,
                                                    Total_videos int,
                                                    Channal_Description text,
                                                    Playlist_Id varchar(80))'''
    cursor.execute(create_query)
    mydb.commit()

    
    single_channel_detail= []
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_channel_detail.append(ch_data["channel_information"])

    df_single_channel_detail=pd.DataFrame(single_channel_detail)  

    for index,row in df_single_channel_detail.iterrows():
      
        insert_query='''insert into channels(Channel_Name,
                                                Channel_Id,
                                                SubscriberCount,
                                                Views,
                                                Total_videos,
                                                Channal_Description,
                                                Playlist_Id
                                                )
                                            
                                                values(%s,%s,%s,%s,%s,%s,%s)'''
        values=(row['Channel_Name'],
                    row['Channel_Id'],
                    row['SubscriberCount'],
                    row['Views'],
                    row['Total_videos'],
                    row['Channal_Description'],
                    row['Playlist_Id'])
        try:
            cursor.execute(insert_query,values)
            mydb.commit()

        except:
                news=f"Your Provided Channel Name {channel_name_s}is Already Exists"

                return news

                                        
    
def playlist_table(channel_name_s):

    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="anthuvan",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    

    create_query='''create table if not exists playlists(playlist_Id varchar(100) primary key,
                                                            Title varchar(100),
                                                            Channel_Id varchar(100),
                                                            Channel_Name varchar(100),
                                                            publishedAt timestamp,
                                                            Video_Count int
                                                            )'''
            
        
    cursor.execute(create_query)
    mydb.commit()


    single_playlist_details=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({"playlist_information.Channel_Name": "tts shalini.s"},{"_id":0,"playlist_information":1}):
      single_playlist_details.append(ch_data["playlist_information"])

    df_single_playlist_details= pd.DataFrame(single_playlist_details[0])

    for index,row in df_single_playlist_details.iterrows():
               
                insert_query='''insert into playlists(playlist_Id,
                                                    Title,
                                                    Channel_Id,
                                                    Channel_Name,
                                                    publishedAt,
                                                    Video_Count
                                                    )

                                               
                                            
                                                    values(%s,%s,%s,%s,%s,%s)'''
            
                values=(row['playlist_Id'],
                        row['Title'],
                        row['Channel_Id'],
                        row['Channel_Name'],
                        row['publishedAt'],
                        row['Video_Count']
                        )
            
                cursor.execute(insert_query,values)
                mydb.commit()

def video_table(channel_name_s):
    mydb=psycopg2.connect(host="localhost",
                                user="postgres",
                                password="anthuvan",
                                database="youtube_data",
                                port="5432")
    cursor=mydb.cursor()


    create_query='''create table if not exists videos(channel_Name varchar(100),
                                                        channel_Id varchar(100),
                                                        video_id varchar(30) primary key,
                                                        Title varchar(150),
                                                        Tags text,
                                                        Thumbnail varchar(200),
                                                        Description text,
                                                        published_Datee timestamp,
                                                        Duration interval,
                                                        Views bigint,
                                                        Likes bigint,
                                                        Comments int,
                                                        Favorite_Count int,
                                                        Definition varchar(10),
                                                        Caption_Status varchar(50)
                                                        )'''
                                                
                
    cursor.execute(create_query)
    mydb.commit()

    single_videos_details=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({"video_information.channel_Name": "tts shalini.s"},{"_id":0,"video_information":1}):
        single_videos_details.append(ch_data["video_information"])

    df_single_videos_details= pd.DataFrame(single_videos_details[0])
    


    for index,row in df_single_videos_details.iterrows():
            insert_query='''insert into videos(channel_Name,
                                                channel_Id,
                                                video_id,
                                                Title,
                                                Tags,
                                                Thumbnail,
                                                Description,
                                                published_Datee,
                                                Duration,
                                                Views,
                                                Likes,
                                                Comments,
                                                Favorite_Count,
                                                Definition,
                                                Caption_Status
                                            )
                                        
                                                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            
            values=(row['channel_Name'],
                    row['channel_Id'],
                    row['video_id'],
                    row['Title'],
                    row['Tags'],
                    row['Thumbnail'],
                    row['Description'],
                    row['published_Datee'],
                    row['Duration'],
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favorite_Count'],
                    row['Definition'],
                    row['Caption_Status'],
                    
                    )
        
    cursor.execute(insert_query,values)
    mydb.commit()


def comments_table(channel_name_s):
    mydb=psycopg2.connect(host="localhost",
                                user="postgres",
                                password="anthuvan",
                                database="youtube_data",
                                port="5432")
    cursor=mydb.cursor()



    create_query='''create table if not exists comments(comment_Id varchar(100) primary key,
                                                        video_id varchar(50),
                                                        comment_Text text,
                                                        comment_Author varchar(150),
                                                        comment_published timestamp
                                                        )'''
                  
               
    cursor.execute(create_query)
    mydb.commit()


    single_comments_details=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({"comment_information.Channel_Name":channel_name_s},{"_id":0,"comment_information":1}):
            single_comments_details.append(ch_data["comment_information"])

    df_single_comments_details=pd.DataFrame(single_comments_details)

    for index,row in df_single_comments_details.iterrows():
                insert_query='''insert into comments(comment_Id,
                                                    video_id,
                                                    comment_Text,
                                                    comment_Author,
                                                    comment_published
                                                    )

                                                
                                                values(%s,%s,%s,%s,%s)'''
            
                values=(row['comment_Id'],
                        row['video_id'],
                        row['comment_Text'],
                        row['comment_Author'],
                        row['comment_published']
                        )
                
    cursor.execute(insert_query,values)
    mydb.commit()

def tables(single_channel):
    news=channels_table(single_channel)
    if news:
         return(news)
    else:
        playlist_table(single_channel)
        video_table(single_channel)
        comments_table(single_channel)

        return "tables created successfully"

def show_channels_table():
    ch_list=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)

    return df

def show_playlists_table():
    pl_list=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])

    df1=st.dataframe(pl_list)

    return df1

def show_videos_table():
    vi_list=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
            for i in range(len(vi_data["video_information"])):
                    vi_list.append(vi_data["video_information"][i])

            df2=st.dataframe(vi_list)

            return df2

def show_comments_table():
   com_list=[]
   db=client["youtube_data"]
   coll1=db["Channel_details"]
   for com_data in coll1.find({},{"_id":0,"comment_information":1}):
            for i in range(len(com_data["comment_information"])):
                  com_list.append(com_data["comment_information"][i])

            df3=st.dataframe(com_list)

            return df3

#streamlit part

with st.sidebar:
    st.title(":red[YOUTUBE DATA HAVERSTING AND WAREHOUSING]")
    st.header("Skill Take Away")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management using MongoDB and SQL")

channel_id=st.text_input("Enter the channet ID")

if st.button("collect and store data"):
    ch_ids=[]
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["Channel_Id"])

    if channel_id in ch_ids:
        st.success("channel Details of the given channel id already exists")
    else:
        insert=Channel_details(channel_id)
        st.success(insert)

    all_channels= []
    db=client["youtube_data"]
    coll1=db["Channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        all_channels.append(ch_data["channel_information"]["Channel_Name"])

    unique_channel=st.selectbox("Select the channel",all_channels)

    if st.button("Migrate to sql"):
        Table=tables(unique_channel)
        st.success(Table)
    
    show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))

    if show_table=="CHANNELS":
        show_channels_table()

    elif  show_table=="PLAYLISTS":
        show_playlists_table()

    elif show_table=="VIDEOS":
        show_videos_table()


    elif show_table=="COMMENTS":
        show_comments_table()



#sql connection

mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="anthuvan",
                        database="youtube_data",
                        port="5432")
cursor=mydb.cursor()

question=st.selectbox("Select your question",("1. All the videos and the channel name",
                                              "2. Channels with most number of videos",
                                              "3. 10 most viewed videos",
                                              "4. Comments in each videos",
                                              "5. Videos with higest likes",
                                              "6. Likes of all videos",
                                              "7. Views of each channel",
                                              "8. Videos published in the year of 2024",
                                              "9. Average duration of all videos in each channel",
                                              "10. Videos with highest number of comments"))

if question=="1. All the videos and the channel name":
    query1='''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)

elif question=="2. Channels with most number of videos":
    query2='''select channel_name as channelname,total_videos as no_videos from channels
                order by total_videos desc'''
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","no_videos"])
    st.write(df2)

elif question=="3. 10 most viewed videos":
    query3='''select views as views,channel_name as channelname,title as videotitle from videos
                where views is not null order by views desc limit 10'''
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channel name","videotitle"])
    st.write(df3)

elif question=="4. Comments in each videos":
    query4='''select comments as no_comments,title as videotitle from videos where comments is not null'''
    cursor.execute(query4) 
    mydb.commit()
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4,columns=["no of comments","videotitle"])
    st.write(df4)

elif question=="5. Videos with higest likes":
    query5='''select title as videotitle,channel_name as channelname,likes as likecount
                from videos where likes is not null order by likes desc'''
    cursor.execute(query5) 
    mydb.commit()
    t5=cursor.fetchall()
    df5=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
    st.write(df5)

elif question=="6. likes of all videos":
    query6='''select likes as likecount,title as videotitle from videos'''
    cursor.execute(query6) 
    mydb.commit()
    t6=cursor.fetchall()
    df6=pd.DataFrame(t6,columns=["likecount","videostitle"])
    st.write(df6)

elif question=="7. Views of each channel":
    query7='''select channel_name as channelname,views as totalviews from channels'''
    cursor.execute(query7) 
    mydb.commit()
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7,columns=["channelname","totalviews"])
    st.write(df7)

elif question=="8. Videos published in the year of 2024":
    query8='''select title as video_title,published_datee as videorelease,channel_name as channelname from videos
                where extract(year from published_datee)=2024'''
    cursor.execute(query8) 
    mydb.commit()
    t8=cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["video_title","published_date","channelname"])
    st.write(df8)

elif question=="9. Average duration of all videos in each channel":
    query9='''select channel_name as channelname,AVG(duration)as averageduration from videos group by channel_name'''
    cursor.execute(query9) 
    mydb.commit()
    t9=cursor.fetchall()
    df9=pd.DataFrame(t9,columns=["channelname","averageduration"])


    T9=[]
    for index,row in df9.iterrows():
        channels_title=row["channelname"]
        average_duration=row["averageduration"]
        average_duration_str=str(average_duration)
        T9.append(dict(channeltitle=channels_title,avgduration=average_duration_str))
    df1=pd.DataFrame(T9)
    st.write(df1)

elif question=="10. Videos with highest number of comments":
    query10='''select title as videotitle,channel_name as channelname,comments as comments from videos where comments is
            not null order by comments desc'''
    cursor.execute(query10) 
    mydb.commit()
    t10=cursor.fetchall()
    print(t10)
    df10=pd.DataFrame(t10,columns=["videotitle","channel name","comments"])
    st.write(df10)
    


    



                                            
    

