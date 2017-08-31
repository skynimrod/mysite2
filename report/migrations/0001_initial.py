# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-15 12:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HolidayTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('holiday', models.DateField(verbose_name='节假日')),
                ('memo', models.CharField(max_length=20, verbose_name='节假日说明')),
            ],
        ),
        migrations.CreateModel(
            name='hzpyTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('py', models.CharField(max_length=6, verbose_name='拼音')),
                ('hz', models.CharField(blank=True, max_length=2, verbose_name='汉字')),
            ],
        ),
        migrations.CreateModel(
            name='ReportDownLoadsInfoTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255, verbose_name='下载地址')),
                ('filename', models.CharField(blank=True, max_length=10, verbose_name='文件名称')),
                ('memo', models.CharField(blank=True, max_length=255, verbose_name='说明')),
            ],
        ),
        migrations.CreateModel(
            name='ReportFilterTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=20, unique=True, verbose_name='关键字')),
                ('flag', models.BooleanField(default=False, verbose_name='是否过滤')),
            ],
        ),
        migrations.CreateModel(
            name='ReportList_2016_Tbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stockcode', models.CharField(max_length=6, verbose_name='股票代码')),
                ('reporturl', models.CharField(max_length=255, unique=True, verbose_name='公告地址')),
                ('reportname', models.CharField(max_length=255, verbose_name='公告名称')),
                ('reporttype', models.CharField(choices=[('pdf', 'pdf file'), ('txt', 'txt file'), ('html', 'html file')], default='pdf', max_length=4, verbose_name='公告类型')),
                ('flag1', models.CharField(max_length=6, verbose_name='待用')),
                ('releaseddate', models.CharField(max_length=10, verbose_name='发布日期')),
                ('releasedtime', models.CharField(max_length=18, verbose_name='发布时间')),
            ],
        ),
        migrations.CreateModel(
            name='ReportListTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stockcode', models.CharField(max_length=6, verbose_name='股票代码')),
                ('reporturl', models.CharField(max_length=255, unique=True, verbose_name='公告地址')),
                ('reportname', models.CharField(max_length=255, verbose_name='公告名称')),
                ('reporttype', models.CharField(choices=[('pdf', 'pdf file'), ('txt', 'txt file'), ('html', 'html file')], default='pdf', max_length=4, verbose_name='公告类型')),
                ('flag1', models.CharField(max_length=6, verbose_name='待用')),
                ('releaseddate', models.CharField(max_length=10, verbose_name='发布日期')),
                ('releasedtime', models.CharField(max_length=18, verbose_name='发布时间')),
            ],
        ),
        migrations.CreateModel(
            name='selfSelectedTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('userid', models.CharField(max_length=20, verbose_name='用户编号')),
                ('groupid', models.CharField(blank=True, max_length=20, verbose_name='组合id')),
                ('groupname', models.CharField(blank=True, max_length=20, verbose_name='组合名称')),
                ('stockcode', models.CharField(max_length=20, verbose_name='')),
            ],
        ),
        migrations.CreateModel(
            name='StockBaseInfoTbl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stockcode', models.CharField(max_length=6, verbose_name='股票代码')),
            ],
        ),
    ]