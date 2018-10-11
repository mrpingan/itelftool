#!/usr/bin/env python
#coding:utf-8

import sys, os, shutil
import os.path
import datetime
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse
from django.http.response import HttpResponse,HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from subprocess import Popen, PIPE
from zabbix.models import MonitorGraph
from zabbix.forms import GraphGroupForm
from urllib import parse


class ZabbixGraph(object):
    def __init__(self, url, name, password):
        self.url = url
        self.name = name
        self.password = password
        cookiejar = http.cookiejar.CookieJar()
        urlOpener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
        values = {"name":self.name,'password':self.password,'autologin':1,"enter":'Sign in'}
        data = urllib.parse.urlencode(values).encode(encoding='UTF8')
        request = urllib.request.Request(url, data)
        try:
            urlOpener.open(request, timeout=10)
            self.urlOpener = urlOpener
        except urllib.error.HTTPError as e:
            print(e)

    def getgraph(self, url, values, image_dir):
        key = values.keys()
        if 'graphid' not in key:
            # print('请确认是否输入graphid')
            sys.exit(1)
        if 'period' not in key:
            values['period'] = 86400
        if 'stime' not in key:
            values['stime'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        if 'width' not in key:
            values["width"] = 800
        if 'height' not in key:
            values["height"] = 200

        data = urllib.parse.urlencode(values).encode(encoding='UTF8')
        request = urllib.request.Request(url, data)
        url = self.urlOpener.open(request)
        image = url.read()
        imagename = "%s/%s.png" % (image_dir, values["graphid"])
        f = open(imagename, 'wb')
        f.write(image)


def get_time_graph(request, starttime, endtime, ids):
    start_time = starttime.strftime('%Y%m%d')
    s_time = starttime.strftime('%Y%m%d%H%M%S')
    end_time = endtime.strftime('%Y%m%d')
    gr_url="http://21.20.48.67:16888/chart2.php"
    indexURL="http://21.20.48.67:16888/index.php"
    username = 'Admin'
    password = 'zabbix'
    image_dir='/var/tmp/monitor/report/%s-%s/png/' % (start_time,end_time)
    
    if os.path.exists(image_dir):
        shutil.rmtree(image_dir)
        
    os.makedirs(image_dir)
    
    period = int((endtime-starttime).total_seconds())
    
    b=ZabbixGraph(indexURL,username,password)
    for id in ids:
        graph_name = 'value_%s' % id
        #print(graph_name)
        graph_name = {"graphid":id,"period":period,"stime":s_time,"width":800,"height":200}
        b.getgraph(gr_url, graph_name, image_dir)
    return image_dir
     
        
def sendgraph_info(request):
    st = request.POST.get('starttime')
    et = request.POST.get('endtime')
    gids = request.POST.get('graphid')
    graphgroups = request.POST.get('graphgroup')
    if graphgroups:
        graphids = graphgroups.split(",")
    elif gids:
        graphids = gids.split(",")
    else:
        return HttpResponse('未手动填写监控图id或未选择监控图组！')

    starttime = datetime.datetime.strptime(st,"%Y-%m-%d %H:%M:%S")
    endtime = datetime.datetime.strptime(et,"%Y-%m-%d %H:%M:%S")
    image_dir = get_time_graph(request, starttime, endtime, graphids)
    
    workdir = os.path.abspath('.')
    example_report = workdir + '/zabbix/example_report/data_report.html'
    
    year = st.split('-')[0]
    month = st.split('-')[1]
    title = year + '年' + month + '月份服务器使用情况报表'
    sed_cmd = "/usr/bin/sed -i " + "'s/Title/" + title + "/g'" + " " + example_report + '&& ' + "/usr/bin/sed -i " + "'s/StartTime/" + st + "/g'" + " " + example_report + "&& " + "/usr/bin/sed -i " + "'s/EndTime/" + et + "/g'" + " " + example_report
    p_sed = Popen(sed_cmd, stdout=PIPE, stderr=PIPE, shell=True)
    p_sed.communicate()
    #sed_cmd2 = "/usr/bin/sed -i " + "'s/StartTime/" + st + "/g'" + " " + example_report
    #sed_cmd3 = "/usr/bin/sed -i " + "'s/EndTime/" + st + "/g'" + " " + example_report
    
    example_report_default = workdir + '/zabbix/example_report/data_report_default.html'
    report_dir = image_dir.split('png')[0]
    report_cmd = 'cp -ar ' + example_report + ' ' +  report_dir + '&& ' + 'cp -ar ' + example_report_default + ' ' +  example_report
    p_report = Popen(report_cmd, stdout=PIPE, stderr=PIPE, shell=True)
    p_report.communicate()
    
    cmd = "cd " + image_dir +" && ls -l"
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    data = p.communicate()
    results = {
        'image_dir':  image_dir,
        'data': data,
        'starttime': starttime,
        'endtime': endtime,
     }
    return render(request, 'zabbix/get_graph_info.html', results)
    

def input_graph_info(request):
    monitor_group = MonitorGraph.objects.all()
    results = {
        'monitor_group': monitor_group,
     }
    return render(request, 'zabbix/input_graph_info.html', results)

    
def graph_group_list(request):
    all_graph_group = MonitorGraph.objects.all()
    results = {
        'all_graph_group':  all_graph_group,
    }
    return render(request, 'zabbix/graph_group_list.html', results)


from zabbix.get_hostinfo import ZabbixAPI
def graph_group_add(request):
    if request.method == "POST":
        groupname = request.POST.get('groupname')
        gids = request.POST.get('graphid')
        graphgroups = request.POST.getlist('graphgroup',[])
        if graphgroups:
            allid = ",".join(graphgroups)
        elif gids:
            allid = gids
        else:
            return HttpResponse('未手动填写监控图id或未选择监控图！')
        
        MonitorGraph.objects.create(groupname=groupname, graphids=allid)
        return HttpResponseRedirect(reverse('graph_group_list'))
        #form = GraphGroupForm(request.POST)
        #if form.is_valid():
        #    form.save()
        #    return HttpResponseRedirect(reverse('graph_group_list'))
    else:
        zapi=ZabbixAPI()
        #token=zapi.UserLogin()
        #print(token)
        hosts=zapi.MyHostGet()
        
        mydictlist = []
        
        for host in hosts:
            mydict = {}
            #print(host)
            hostid = host['hostid']
            hostname = host['host']
            graphinfo = host['graphs']
            #print(hostid,hostname,graphinfo)
            for graph in graphinfo:
                mydict.update({'hostname':hostname, 'hostid':hostid, graph['name']:graph['graphid']})
            mydictlist.append(mydict)
        #form = GraphGroupForm()

    results = {
        #'form': form,
        'mydictlist': mydictlist,
        'request': request,
    }

    return render(request, 'zabbix/graph_group_add.html', results)


def graph_group_edit(request, ids):
    graph_group = MonitorGraph.objects.get(id=ids)
    if request.method == "POST":
        form = GraphGroupForm(request.POST, instance=graph_group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('graph_group_list'))
    else:
        form = GraphGroupForm(instance=graph_group)

    results = {
        'ids': ids,
        'form': form,
        'request': request,
    }
    return render(request, 'zabbix/graph_group_edit.html', results)


def graph_group_del(request, ids):
    MonitorGraph.objects.filter(id=ids).delete()
    return HttpResponseRedirect(reverse('graph_group_list'))



def graph_upload(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理  
        myFiles =request.FILES.getlist("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        image_dir = request.POST.get('image_dir')
        for myFile in myFiles:
            destination = open(os.path.join(image_dir,myFile.name),'wb+')    # 打开特定的文件进行二进制的写操作  
            for chunk in myFile.chunks():      # 分块写入文件  
                destination.write(chunk)  
            destination.close()
        
        report_dir = image_dir.split('png')[0]
        data_info = image_dir.split('report/')[1].split('/png')[0]
        zip_cmd = 'cd ' + report_dir + ' ' + '&& ' + 'zip -r ' + 'Report_' + data_info + '.zip ' + './*'
        zip_report = Popen(zip_cmd, stdout=PIPE, stderr=PIPE, shell=True)
        zip_report.communicate()
        
        z_name = report_dir + 'Report_' + data_info + '.zip'
        z_file = open(z_name, 'rb')
        data = z_file.read()
        z_file.close()
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment;filename=' + parse.quote(z_name.split('/')[-1])
        return response
        

