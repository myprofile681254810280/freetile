import logging

from .config import (exclude_wm_class, exclude_wm_name, min_window_height,
                     min_window_width)
from .helper import xcb
from .helper import xlib as xlibhelper
from .helper.helper_ewmh import (get_window_list, maximize_window,
                                 raise_window, unmaximize_windows)
from .helper.xlib import disp, get_frame_extents
from .workarea import workarea


class WindowList:
    windowInCurrentWorkspaceInStackingOrder = []
    windowGeometry = {}
    windowName = {}
    minGeometry = {}
    windowObjectMap = {}
    ewmhactive = None

    def maximize_window(self, winid):
        win = self.windowObjectMap[winid]
        geo = win.get_geometry()
        if not workarea.windowInCurrentViewport(geo):
            from .monitor import monitor
            if monitor.available:
                xcb.move(winid, monitor.x, monitor.y)
            else:
                xcb.move(winid, 0, 0)
        logging.info('maximize window')
        maximize_window(win, sync=False)

    def raise_window(self, winid):
        logging.debug('raise window %s', winid)
        win = self.windowObjectMap[winid]
        raise_window(win)

    def reset(self, ignore=[]):
        desktop = xlibhelper.get_current_workspace()
        self.ewmhactive = xlibhelper.get_active_window()
        self.windowInCurrentWorkspaceInStackingOrder = []
        self.windowName = {}
        self.windowGeometry = {}
        self.minGeometry = {}
        self.windowObjectMap = {}

        for win, _desktop, name in get_window_list(ignore):
            winid = win.id
            self.windowObjectMap[winid] = win
            if not _desktop == desktop:
                continue
            if name in exclude_wm_name:
                continue

            if not {
                    disp.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
            }.isdisjoint(xlibhelper.getWmState(win)):
                continue

            if not {disp.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')}.isdisjoint(xlibhelper.getWmWindowType(win)):
                continue

            wmclass, minimized = xlibhelper.get_wm_class_and_state(win)
            if minimized:
                continue
            wmclass = set(wmclass)
            if not wmclass == wmclass - set(exclude_wm_class):
                continue

            self.windowName[winid] = name

            geo = win.get_geometry()
            o = self.get_absolute_geo(win)

            # window in current viewport?
            if not workarea.windowInCurrentViewport(geo, threshold=0.1):
                continue

            wnh = win.get_wm_normal_hints()
            f_left, f_right, f_top, f_bottom = get_frame_extents(win)
            minw = max(min_window_width, wnh.min_width + f_left, f_right)
            minh = max(min_window_height, wnh.min_height + f_top, f_right)
            self.minGeometry[winid] = minw, minh

            self.windowInCurrentWorkspaceInStackingOrder.append(winid)

    def get_absolute_geo(self, win):
        if win.id not in self.windowGeometry:
            geo = win.get_geometry()
            f_left, f_right, f_top, f_bottom = get_frame_extents(win)
            opaque_region = xlibhelper.get_wm_opaque_region(win)

            self.windowGeometry[win.id] = [
                geo.x - f_left + opaque_region[4],
                geo.y - f_top + opaque_region[1],
                geo.width + f_left + f_right - opaque_region[4] - opaque_region[4],
                geo.height + f_top + f_bottom - opaque_region[1] - opaque_region[4] - opaque_region[4],
            ]
            p = win.query_tree().parent
            if p:
                pgeo = self.get_absolute_geo(p)
                self.windowGeometry[win.id][0] += pgeo[0]
                self.windowGeometry[win.id][1] += pgeo[1]
        return self.windowGeometry[win.id]

    def get_current_layout(self):
        return [self.windowGeometry[opaque_regiond] for opaque_regiond in self.windowInCurrentWorkspaceInStackingOrder]

    def get_active_window(self, allow_outofworkspace=False):
        active = self.ewmhactive
        if active is None:
            return None
        active = active.id
        if active in self.windowInCurrentWorkspaceInStackingOrder:
            return active
        if allow_outofworkspace and active in self.windowName:
            return active

    def arrange(self, layout, windowids):
        windows = [self.windowObjectMap[wid] for wid in windowids]
        # unmaximize
        unmaximize_windows(windows)

        layout_final = []
        # move windows
        for win, lay, in zip(
                windows,
                layout,
        ):
            normal_hints = win.get_wm_normal_hints()

            x, y, width, height = lay
            f_left, f_right, f_top, f_bottom = get_frame_extents(win)
            width -= f_left + f_right
            height -= f_top + f_bottom

            # window gravity: Static
            if normal_hints.win_gravity == 10:
                y += f_top
                x += f_left
            opaque_region = xlibhelper.get_wm_opaque_region(win)
            x -= opaque_region[4]
            width += opaque_region[4] + opaque_region[4]
            y -= opaque_region[1]
            height += opaque_region[1] + opaque_region[4] + opaque_region[4]
            layout_final.append([x, y, width, height])
        return xcb.arrange(layout_final, windowids)


windowlist = WindowList()
