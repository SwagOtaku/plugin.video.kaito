# -*- coding: utf-8 -*-

from resources.lib.ui import maintenance
from resources.lib.ui import database_sync
from resources.lib.ui import monitor

database_sync.AnilistSyncDatabase()
maintenance.run_maintenance()
monitor.SettingsMonitor()
