# coding=utf-8
from __future__ import absolute_import


import octoprint.plugin
import sarge
import flask
import urllib2
import os
from subprocess import Popen, PIPE

class PantiltPlugin(octoprint.plugin.SettingsPlugin,
                    octoprint.plugin.AssetPlugin,
                    octoprint.plugin.TemplatePlugin,
                    octoprint.plugin.SimpleApiPlugin,
                    octoprint.plugin.StartupPlugin):

	def __init__(self):
		self.panValue = 0
		self.tiltValue = 0
		self.pan_=0
		self.tilt_=0
		self.pantiltHandlers = None

	def on_after_startup(self):
		self.pantiltHandlers = self._plugin_manager.get_hooks("octoprint.plugin.pantilt_handler")
		self.panValue=int(self._settings.get(["pan", "initialValue"]))
		self.tiltValue=int(self._settings.get(["tilt", "initialValue"]))
		self.pan_=self.panValue
		self.tilt_=self.tiltValue
		self.inival=[self.panValue,self.tiltValue]
		self.stepmotor=int(self._settings.get(["stepmotor"]))
		
	def get_template_configs(self):
		return [
		    dict(type="settings", custom_bindings=False)
		]

	##~~ SettingsPlugin mixin
	def get_settings_defaults(self):
		return dict(
			stepmotor=10,
			pan=dict(
				initialValue=50,
				minValue=0,
				maxValue=180,
				invert=False
			),
			tilt=dict(
				initialValue=50,
				minValue=0,
				maxValue=180,
				invert=False,
			),
		)

	def callScript(self, panValue, tiltValue):
		panmin=int(self._settings.get(["pan", "minValue"]))
		panmax=int(self._settings.get(["pan", "maxValue"]))
		tiltmax=int(self._settings.get(["tilt", "maxValue"]))
		tiltmin=int(self._settings.get(["tilt", "minValue"]))
		if panValue<panmin:
			panValue=panmin
		elif panValue>panmax:
			panValue=panmax
		self.panValue=panValue
		
		if tiltValue<tiltmin:
			tiltValue=tiltmin
		elif tiltValue>tiltmax:
			tiltValue=tiltmax
		self.tiltValue=tiltValue
		
		# if there are anly pantilt handlers, loop through them, then return
		if len(self.pantiltHandlers) > 0:
			values = {'pan': self.panValue, 'panMin': self._settings.get(["pan", "minValue"]),
					  'panMax': self._settings.get(["pan", "maxValue"]),
					  'tilt': self.tiltValue, 'tiltMin': self._settings.get(["tilt", "minValue"]),
					  'tiltMax': self._settings.get(["tilt", "maxValue"])}
			for name, handler in self.pantiltHandlers.items():
				handler(values)
			return

		self._logger.info(
                        "start motor pan: %s tilt %s",panValue, tiltValue)
		
		script = os.path.dirname(os.path.realpath(__file__)) + "/stepmotor.py "
		
		try:
			relpan=panValue-self.pan_
			reltilt=tiltValue-self.tilt_

			cmd = "sudo python " + script +" -r 10 -a " + str(relpan) + " -b " + str(reltilt)
			Popen(cmd, shell=True)
			self._logger.info("new val pan tilt: "+str(relpan)+" "+str(reltilt))
			
			self.pan_=panValue
			self.tilt_=tiltValue
		except Exception, e:
			error = "Command failed: {}".format(str(e))
			self._logger.warn(error)

	##~~ AssetPlugin mixin
	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/pantilt.js"],
			css=["css/pantilt.css"],
			less=["less/pantilt.less"]
		)

	##~~ SimpleApiPlugin mixin
	def get_api_commands(self):
		return dict(
			set =[],
			left=[],
			right=[],
			up=[],
			down=[],
			home=[]
		)

	def on_api_command(self, command, data):
		if command == "set":
			if "panValue" in data:
				panValue = int(data["panValue"])
			if "tiltValue" in data:
				tiltValue = int(data["tiltValue"])
			self.callScript(panValue, tiltValue)
		elif command =="sethome":
			if "panValue" in data:
				panValue = int(data["panValue"])
			if "tiltValue" in data:
				tiltValue = int(data["tiltValue"])
				
			self.pan_= panValue
			self.tilt_= tiltValue
		elif command == "left" or command == "right":
			panValue = self.panValue

			stepSize = self.stepmotor
			if stepSize in data:
				stepSize = int(data["stepSize"])

			if self._settings.get(["pan", "invert"]):
				panValue = panValue - (stepSize if command == "right" else -stepSize)
			else:
				panValue = panValue + (stepSize if command == "right" else -stepSize)

			self.callScript(panValue, self.tiltValue)
		elif command == "up" or command == "down":
			tiltValue = self.tiltValue

			stepSize = self.stepmotor
			if stepSize in data:
				stepSize = int(data["stepSize"])

			if self._settings.get(["tilt", "invert"]):
				tiltValue = tiltValue - (stepSize if command == "up" else -stepSize)
			else:
				tiltValue = tiltValue + (stepSize if command == "up" else -stepSize)

			self.callScript(self.panValue, tiltValue)
		elif command == "home":
			panValue=self.inival[0]
			tiltValue=self.inival[1]
			self.callScript(panValue, tiltValue)
		
	def on_api_get(self, request):
		return flask.jsonify(panValue=self.panValue, tiltValue=self.tiltValue)

	##~~ Softwareupdate hook
	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			pantilt=dict(
				displayName="Pantilt Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="Domo-Com",
				repo="OctoPrint-PanTilt",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/Domo-Com/OctoPrint-PanTilt/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Pantilt"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PantiltPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

