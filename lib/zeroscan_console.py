#!/usr/bin/env python
# -*- coding:utf-8 -*-

import cmd
import os
import subprocess
from lib.core import logger
from lib.core.manager import PluginManager
from lib.thirdparty.colorama import init,Fore

init()

class Interface(cmd.Cmd, PluginManager):
    """
    ZEROScan 核心类
    """
    def __init__(self):
        cmd.Cmd.__init__(self)
        PluginManager.__init__(self)
        self.prompt = "ZEROScan > "

    def do_help(self, line):
        """
        帮助
        :return:
        """
        commands = {
            "help": "Help menu",
            "version": "Show the framework version numbers",
            "list": "List all plugins",
            "search <keyword>": "Search plugin names and descriptions",
            "info <plugin>": "Display information about one plugin",
            "use <plugin>": "Select a plugin by name",
            "options": "Display options for current plugin",
            "set <option> <value>": "Set a variable to a value",
            "exploit": "Run current plugin",
            "vulns": "List all vulnerabilities in the database",
            "vulns -d": "Clear all vulnerabilities in the database",
            "vulns -o <plugin>": "Save vulnerabilities to file",
            "update": "Update the framework",
            "rebuild": "Rebuild the database",
            "exit": "Exit the console"
        }
        print "\nCore Commands\n=============\n"
        print "%-30s%s" % ("Command", "Description")
        print "%-30s%s" % ("-------", "-----------")
        for command in commands:
            print "%-30s%s" % (command, commands[command])
        print

    def do_version(self, line):
        """
        版本信息
        :return:
        """
        print
        print "Version: %s" % self.version()
        print "CMS: %d" % self.CMSNum()
        print "Modules: %d" % self.PluginsNum()
        print

    def do_list(self, line):
        """
        插件列表
        :return:
        """
        print "\Modules\n=======\n"
        print "%-40s%-40s%s" % ("Name", "Scope", "Description")
        print "%-40s%-40s%s" % ("----", "-----", "-----------")
        for name, scope, description in self.ListPlugins():
            print "%-40s%-40s%s" % (name, scope, description)
        print

    def do_search(self, keyword):
        """
        搜索插件
        :param keyword: string, 关键字
        :return:
        """
        if keyword:
            print "\nMatching Modules\n================\n"
            print "%-40s%-40s%s" % ("Name", "Scope", "Description")
            print "%-40s%-40s%s" % ("----", "-------", "-----------")
            for name, scope, description in self.SearchPlugin(keyword):
                print "%-40s%-40s%s" % (name, scope, description)
            print
        else:
            logger.error("search <keyword>")

    def do_info(self, plugin):
        """
        插件信息
        :param plugin: string, 插件名称
        :return:
        """
        if not plugin:
            if self.CurrentPlugin:
                plugin = self.CurrentPlugin
            else:
                logger.error("info <plugin>")
                return
        if self.InfoPlugin(plugin):
            name, author, cms, scope, description, reference = \
                self.InfoPlugin(plugin)
            print "\n%15s: %s" % ("Name", name)
            print "%15s: %s" % ("CMS", cms)
            print "%15s: %s\n" % ("Scope", scope)
            print "Author:\n\t%s\n" % author
            print "Description:\n\t%s\n" % description
            print "Reference:\n\t%s\n" % reference
        else:
            logger.error("Invalid plugin: %s" % plugin)

    def complete_info(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        plugins = [i[0] for i in self.ListPlugins()]
        if not text:
            completions = plugins
        else:
            completions = [p for p in plugins if p.startswith(text)]
        return completions

    def do_use(self, plugin):
        """
        加载插件
        :param plugin: string, 插件名称
        :return:
        """
        if plugin:
            try:
                self.LoadPlugin(plugin)
            except Exception:
                logger.error("Failed to load plugin: %s" % plugin)
            if self.CurrentPlugin:
                self.prompt = "ZEROScan exploit({color}{content}{color_reset}) > ".format(
                    color=Fore.RED, content=self.CurrentPlugin, color_reset=Fore.RESET)
        else:
            logger.error("use <plugin>")

    def complete_use(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        plugins = [i[0] for i in self.ListPlugins()]
        if not text:
            completions = plugins
        else:
            completions = [p for p in plugins if p.startswith(text)]
        return completions

    def do_options(self, line):
        """
        插件设置项
        :return:
        """
        if self.CurrentPlugin:
            rn = self.ShowOptions()
            if isinstance(rn, str):
                logger.error(rn)
            else:
                print "\n\t%-20s%-40s%-10s%s" % ("Name", "Current Setting",
                                                 "Required", "Description")
                print "\t%-20s%-40s%-10s%s" % ("----", "---------------",
                                               "--------", "-----------")
                for option in rn:
                    print "\t%-20s%-40s%-10s%s" % (option["Name"],
                                                   option["Current Setting"],
                                                   option["Required"],
                                                   option["Description"])
                print
        else:
            logger.error("Select a plugin first.")

    def do_set(self, arg):
        """
        设置参数
        :param arg: string, 以空格分割 option, value
        :return:
        """
        if self.CurrentPlugin:
            if len(arg.split()) == 2:
                option = arg.split()[0]
                value = arg.split()[1]
                rn = self.SetOption(option, value)
                if rn.startswith("Invalid option:"):
                    logger.error(rn)
                else:
                    print rn
            else:
                logger.error("set <option> <value>")
        else:
            logger.error("Select a plugin first.")

    def complete_set(self, text, line, begidx, endidx):
        """
        tab 补全
        :return:
        """
        text = text.lower()
        options = [i["Name"] for i in self.ShowOptions()]
        if not text:
            completions = options
        else:
            completions = [o for o in options if o.lower().startswith(text)]
        return completions

    def do_exploit(self, line):
        """
        执行插件
        :return:
        """
        if self.CurrentPlugin:
            rn = self.ExecPlugin()
            if not rn[0]:
                logger.error(rn[1])
        else:
            logger.error("Select a plugin first.")

    def do_vulns(self, arg):
        """
        漏洞信息
        :param arg: string, 参数
        :return:
        """
        arg = arg.split()
        if not arg:
            vulns = self.ShowVulns()
            print "\nVulns\n=====\n"
            print "%-40s%s" % ("Plugin", "Vuln")
            print "%-40s%s" % ("------", "----")
            for plugin, vuln in vulns:
                print "%-40s%s" % (plugin, vuln)
            print
        elif arg[0] == "-d":
            self.ClearVulns()
            logger.success("Clear database successfully.")
        elif arg[0] == "-o":
            plugin_name = arg[1]
            vulns = self.ShowVulns()
            with open("vulns.txt", "a") as f:
                f.write(os.linesep)
                f.write("[%s]" % plugin_name + os.linesep)
                for i in vulns:
                    if i[0] == plugin_name:
                        f.write(i[1]+os.linesep)
                f.write(os.linesep)
            logger.success("Save vulns successfully.")

    def do_rebuild(self, line):
        """
        重建数据库
        :return:
        """
        logger.process("Clear current database")
        logger.process("Rebuild database")
        self.DBRebuild()
        logger.success("OK")

    def do_update(self, line):
        """
        更新
        :return:
        """
        logger.process("")
        logger.process("Attempting to update the ZEROScan")
        logger.process("")
        logger.process("Downloading plugin list")
        remote_plugins = self.DownPluginList()
        logger.process("Getting local plugin list")
        local_plugins = self.GetLocalPluginList()
        logger.process("Comparing and updating")
        new_plugins = self.DownPlugins(remote_plugins, local_plugins)
        logger.success("New plugins: %s" % str(new_plugins))
        self.do_rebuild("")

    def do_back(self, line):
        """
        返回主菜单
        :param line:
        :return:
        """
        self.current_plugin = ""
        self.prompt = "ZEROScan > "

    def do_shell(self, arg):
        """
        执行系统命令
        :param arg:
        :return:
        """
        logger.process("exec: %s" % arg)
        SubCmd = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        print
        print SubCmd.communicate()[0]

    def default(self, line):
        """
        无法识别命令时
        :param line:
        :return:
        """
        logger.error("Unknown command: %s" % line)

    def do_exit(self, line):
        """
        退出
        :return:
        """
        self.Exit()
        exit()

    def emptyline(self):
        """
        空行
        :return:
        """
        pass
