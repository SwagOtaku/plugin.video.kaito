# -*- coding: utf-8 -*-
"""
    Made by umbrelladev 10-6-22
    Added by Goldenfreddy0703 5-15-23
"""
from resources.lib.windows.base import BaseDialog


class TextViewerXML(BaseDialog):

    def __init__(self, *args, **kwargs):
        BaseDialog.__init__(self, args)
        self.window_id = 2060
        self.heading = kwargs.get('heading')
        self.text = kwargs.get('text')

    def run(self):
        self.doModal()
        self.clearProperties()

    def onInit(self):
        self.set_properties()
        self.setFocusId(self.window_id)

    def onAction(self, action):
        if action in self.closing_actions or action in self.selection_actions:
            self.close()

    def set_properties(self):
        self.setProperty('otaku.text', self.text)
        self.setProperty('otaku.heading', self.heading)
