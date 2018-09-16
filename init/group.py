#!/usr/bin/env python
#coding: utf-8

#from __future__ import division
import os
import time
import datetime
import threading
import schedule
import ConfigParser
import re
import sys
from wxpy import *
from xpinyin import Pinyin


from init import analyze
from init import express

reload(sys)
sys.setdefaultencoding('utf8')


class GroupMessage():
    #从配置文件获取参数，初始化变量
    def __init__(self):
        cf = ConfigParser.ConfigParser()
        cf.read('config/wechat.conf')
        self.path = cf.get('wechat', 'path')
        group_names = cf.get('wechat', 'group_name').decode('utf-8')
        self.group_list=group_names.strip(',').split(',')
        self.friend_name = cf.get('wechat','friends').decode('utf-8')
        self.newcomer = cf.get('wechat','newcomer')
        self.recev_mps = int(cf.get('wechat','recev_mps'))
        self.use_xiaoi = int(cf.get('wechat','xiaoi'))
        self.key = cf.get('wechat','key')
        self.secret = cf.get('wechat','secret')
    
        group_note = cf.get('wechat', 'group_note').decode('utf-8')
        self.group_note_list=group_note.strip(',').split(',')
        group_newcomer = cf.get('wechat', 'group_newcomer').decode('utf-8')
        self.group_newcomer_list=group_newcomer.strip(',').split(',')
        self.send_time = cf.get('wechat', 'send_time').decode('utf-8')
     
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        self.talk_path = os.path.join(self.path, 'talks')
        if not os.path.exists(self.talk_path):
            os.mkdir(self.talk_path)


        self.xiaoi = XiaoI(self.key, self.secret)
        

        self.send_me = 11

    def login(self):
        self.bot = Bot(cache_path=True, console_qr=True)
        self.myself = self.bot.self
        self.friend = self.bot.friends().search(self.friend_name)[0]
        #print self.bot.friends()
        print self.bot.groups()
        #print self.bot.mps()
       

    #处理公共号消息
    def my_mps(self):
        @self.bot.register(MP)
        def print_mp_msg(msg):
            #print msg
            #print dir(msg)
            self.friend.send(msg)
            #msg.forward(self.friend)
            if msg.type == SHARING and msg.sender.name == '爱净意':
                for article in msg.articles:
                    if '妹子篇' in article.title:
                        #article.forward(self.friend)
                        self.friend.send(article.title)
                        self.friend.send(article.url)
                    if  '妹子' in article.title and '现居北京' in article.title:
                        self.friend.send(article.title)
                        self.friend.send(article.url)
            if msg.type == SHARING and msg.sender.name == '硕士博士俱乐部':
                for article in msg.articles:
                    if '妹子篇' in article.title:
                        self.friend.send(article.title)
                        self.friend.send(article.url)
            if msg.type == SHARING and msg.sender.name == '硕博联谊':
                for article in msg.articles:
                    if  '妹子' in article.title and '现居北京' in article.title:
                        self.friend.send(article.title)
                        self.friend.send(article.url)

        
    #处理群消息
    def group_msg(self,group_n,group):
        #将中文群转化为拼音
        group_zh = Pinyin()
        group_zh_name  = group_zh.get_pinyin(group_n)
        log_file = os.path.join(self.path,group_zh_name)
        if not os.path.exists(log_file):
            os.mkdir(log_file)
        #注册消息
        @self.bot.register(group)
        def print_msg(msg):
            #print msg, msg.type
            #日志文件创建
            day = time.strftime("%Y-%m-%d")
            file_name = '%s.txt' % ( day)
            file_ab_path = os.path.join(log_file, file_name)
            #pic_file = 'log/%s-%s' % (group_zh_name,day)
            pic_file = os.path.join(self.path,group_zh_name,day)
            if not os.path.exists(pic_file):
                os.mkdir(pic_file)
    
            create_time = msg.create_time.strftime('%Y-%m-%d %H:%M:%S')
            name = msg.member.name
            #群内有被at的消息就会智能回复，支持图灵和小i机器人，默认小i
            #print msg.is_at
            #print self.use_xiaoi
            if msg.is_at and self.use_xiaoi == 1:
                #tuling = Tuling(api_key=self.key)
                #tuling.do_reply(msg)
                if u'，表情包' in msg.text:
                    new_msg_total = msg.text.split(u'表情包')[1]
                    #msg.reply(new_msg)
                    pic_num = new_msg_total[0:1]
                    if pic_num == '1':
                        new_msg = new_msg_total[1:]
                    else:
                        new_msg = new_msg_total
                    express.Make_express().make_pic(new_msg,pic_num)
                    #msg.reply_image('material/target.jpg')
                    msg.reply('@img@material/target.jpg')
                    myself_text = new_msg
                else:
                    myself_text = self.xiaoi.do_reply(msg)
                myword = "%s %s:%s\n" % (create_time, self.myself.name, myself_text)
                
            #消息处理，TEXT文本，SHARING链接，PICTURE图片，RECORDING语音，
            #ATTACHMENT附件，NOTE红包提示，新人入群提示，MAP地图
            if msg.type == TEXT:
                word = "%s %s:%s\n" % (create_time, name, msg.text)
            elif msg.type == SHARING:
                #print  msg
                word = "%s %s:SHARING:%s\n" % (create_time, name, msg.text)
                
            elif msg.type in [PICTURE, VIDEO,RECORDING,ATTACHMENT]:
                ct = msg.create_time.strftime('%Y-%m-%d-%H-%M-%S')
                if msg.type == PICTURE:
                    #print msg.raw
                    msg.get_file('%s/%s-%s' % (pic_file,ct,msg.file_name))
                    word = "%s %s:PICTURE:%s\n" % (create_time, name, msg.file_name)
                #elif msg.type == VIDEO:
                 #  msg.get_file('%s/%s-%s-%s' % (file_name,ct,name,msg.file_name))
                elif msg.type == RECORDING:
                    #print name
                    msg.get_file('%s/%s-%s-%s' % (pic_file,ct,name,msg.file_name))
                    word = "%s %s:RECORDING:%s\n" % (create_time, name, msg.file_name)
                elif msg.type == ATTACHMENT:
                    #print msg.file_name
                    msg.get_file('%s/%s-%s-%s' % (pic_file,ct,name,msg.file_name))
                    word = "%s %s:ATTACHMENT:%s\n" % (create_time, name, msg.file_name)
            elif msg.type == NOTE:
                if u'\u9080\u8bf7' in msg.text and self.newcomer == '1':
                    if group_n in self.group_newcomer_list: 
                        new_name = msg.text.split('"')[-2]
                        #print 'Newcomer .......................'
                        #msg.reply_image('material/newcomer.jpg')
                    
                        newcomer = """@%s 欢迎新人进入本群，请文明聊天。\n进群请修改备注：城市-出生年-性别-读书（工作）-姓名，复制如下模板修改即可。"""% (new_name)
                        newcomer1 = '北京-90-女-医药-默默'
                        msg.reply(newcomer)
                        time.sleep(2)
                        msg.reply(newcomer1)
                    #myword = "%s %s:%s\n" % (create_time, self.myself.name, newcomer)
                if u'\u6536\u5230' in msg.text:
                    #print 'red packages!!!!!!!!!!!!!!!!!!!!!!'
                    self.friend.send('Red Package:%s' %(group_n))
                word = "%s %s:NOTE:%s\n" % (create_time, name, msg.text)
            elif msg.type == CARD:
                word = "%s %s:CARD:%s\n" % (create_time, name, msg.text)
            elif msg.type == MAP:
                word = "%s %s:MAP:%s\n" % (create_time, name, msg.text)
            elif msg.type == SYSTEM:
                word = "%s %s:SYSTEM:%s\n" % (create_time, name, msg.text)
    
            if word:
                with open(file_ab_path, "a+") as f:
                    f.write(word.encode('utf-8'))
                    if myword:
                        f.write(myword.encode('utf-8'))
                    word = None
            #msg.forward(self.friend)
    #记录日志
    def log_message(self,group_zh_name, word):
        log_file = os.path.join(self.path,group_zh_name)
        if not os.path.exists(log_file):
            os.mkdir(log_file)
        

        #日志文件创建
        day = time.strftime("%Y-%m-%d")
        file_name = '%s.txt' % ( day)
        file_ab_path = os.path.join(log_file, file_name)
        pic_file = os.path.join(self.path,group_zh_name,day)
        if not os.path.exists(pic_file):
            os.mkdir(pic_file)
    
        with open(file_ab_path, "a+") as f:
            f.write(word.encode('utf-8'))
            word = None


    #发送定时任务
    def send_message(self):
        #group_n = '测试专用群'.decode('utf-8')
        for group_n in self.group_note_list:
            try:
                my_group = self.bot.groups().search(group_n)[0]
            except IndexError,e:
                print '%s not exists, please check it!' %val
            #print my_group
            #print_time = time.asctime( time.localtime(time.time()) )
            #print my_group
            #my_group.update_group(True)
            #group_mem_stats = my_group.members.stats_text()
            #my_group.send_image('material/meinv.jpg')

            #输入昨日发言人数和次数
            group_zh = Pinyin()
            group_zh_name  = group_zh.get_pinyin(group_n)
            members_list = []
            for members in my_group:
                members_list.append(members.name)
            analyze.GroupLog(group_zh_name,self.path).log_members(members_list)
            members_l = analyze.GroupLog(group_zh_name,self.path).output_members()
            #print members_list
            #print members_l
            if members_l == 0 or members_l == members_list:
                member_word = '群内没有人员变动。'
            else:
                out_nums = 0
                in_nums = 0
                out_mem = ''
                for i in members_list:
                    if i not in members_l:
                        in_nums +=1
                for i in members_l:
                    if i not in members_list:
                        out_mem = out_mem + i + '\n'
                        out_nums +=1
                if out_nums == 0:
                    out_word = '没有人离开。'
                else:
                    #out_word = '有%s人离开了。\n离开的人有：\n%s' %(out_nums, out_mem)
                    out_word = '有%s人离开了。' %(out_nums)
                   
                if in_nums == 0:
                    in_word = '没有人进来，'
                else:
                    in_word = '有%s人来了，' %(in_nums)
                member_word = in_word + out_word
            #print member_word
             

            grouplog = analyze.GroupLog(group_zh_name,self.path)
            nums = grouplog.log_context()
            if nums[0] == 0:
                print_nums = '昨天没有人发言。'
            else:
                print_nums = '昨天有%s人在群内侃侃而谈%s句。' %(nums[0],nums[1])
            talks_total = print_nums + '\n\n' + nums[2]
            if self.send_me == 1:
                self.friend.send(group_n)
                #self.friend.send(group_mem_stats)
                #self.friend.send_image('material/zaoan.png')
                self.friend.send('Good morning!')
                for me_num in [member_word, talks_total]:
                    self.friend.send(me_num)
              
            else:
                #my_group.send(group_mem_stats)
                create_time = time.strftime('%Y-%m-%d %H:%M:%S')
                #my_group.send_image('material/zaoan.png')
                my_group.send('早上好！')
                word = "%s %s:Good Morning!\n" % (create_time, self.myself.name)
                self.log_message(group_zh_name, word)
                for group_num in [member_word, talks_total]:
                    time.sleep(2)
                    my_group.send(group_num)
                word = "%s %s:%s\n" % (create_time, self.myself.name, member_word)
                self.log_message(group_zh_name, word)
                #word = "%s %s:%s\n" % (create_time, self.myself.name, print_nums)
                #self.log_message(group_zh_name, word)
                word = "%s %s:%s\n" % (create_time, self.myself.name, talks_total)
                self.log_message(group_zh_name, word)

    #使用schedule模块执行定时任务
    def use_sche(self):
        if self.send_me == 1:
            self.send_message()
        #schedule.every().day.at("5:00").do(self.send_message)
        #schedule.every().day.at("17:02").do(self.send_message)
        schedule.every().day.at(self.send_time).do(self.send_message)
        while True:
            #self.myself.send('log out')
            if not self.bot.alive:
                print 'not login'
                self.main()
            schedule.run_pending()
            time.sleep(10)
    
    #进入群聊接受消息 
    def run_task(self):            
        #my_groups = []
        for i,val in enumerate(self.group_list):
            print val
            try:
                my_group = self.bot.groups().search(val)[0]
                self.group_msg(self.group_list[i],my_group)
            except IndexError,e:
                print '%s not exists, please check it!' %val
        embed()
        #self.bot.join()
            
    def main(self):
        self.login()
        #threads = []
        t1 = threading.Thread(target=self.run_task,args=())
        t1.setDaemon(True)
        t1.start()
        if self.recev_mps == 1:
            t2 = threading.Thread(target=self.my_mps,args=())
            t2.setDaemon(True)
            t2.start()

        t3 = threading.Thread(target=self.use_sche(),args=())
        #t3.setDaemon(True)
        t3.start()

        #embed()

if __name__ == "__main__":
    group_m = GroupMessage()
    group_m.main()   

