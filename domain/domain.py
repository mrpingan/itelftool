#!/usr/bin/evn python
#coding:utf-8

import requests
from bs4 import BeautifulSoup
import re
import datetime
import urllib


result2=[]
def get_domain_info(k,i):
    if 'http://' in  i :
        i = i[7:]
    url = 'http://seo.chinaz.com/{}'.format(i)
    req = urllib.request.Request(url=url)
    req_data = urllib.request.urlopen(req)
    text = req_data.read()
    soup = BeautifulSoup(text, 'html.parser')

    try:
        ret_time = soup.find('div', class_='w97-0 brn col-hint02 pl0').text.split('于')[1].split(',')
        domain_age = soup.find('div', class_='w97-0 brn col-hint02 pl0').text.split('（')[0]
        ctime = ret_time[0][:-1].replace('年', '-').replace('月', '-')+ ' 00:00'
        etime = ret_time[1].split('为')[1][:-2].replace('年', '-').replace('月', '-')+ ' 00:00'
        domain_record_num = soup.find('a', href = re.compile('ICP')).text
        domain_record = soup.findAll('strong')
        domain_nature = domain_record[0].text
        domain_company = domain_record[1].text

        try:
            lis = soup.find('div', class_='brn ipmW').text
            lis_ip = (lis[3:].split('['))[0]
            ip_source = (lis[3:].split('['))[1].split(']')[0]
        except Exception as e:
            print("没有IP", e)
            lis_ip = '0.0.0.0'
        a = {'name':i, 'ip_source':ip_source, 'ip':lis_ip, 'ctime':ctime, 'etime':etime, 'domain_age':domain_age, 'domain_record_num':domain_record_num, 'domain_nature':domain_nature, 'domain_company':domain_company, 'comment':k}
        result2.append(a)
    except Exception as e:
        #print("域名没查到",e)
        b = {'name':i,'ipd':'0.0.0.0','ctime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M') ,'etime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),'comment':k }
        result2.append(b)
    #print(result2)
    return result2

    
