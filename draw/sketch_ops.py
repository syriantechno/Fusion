# -*- coding: utf-8 -*-
"""
AlumProCNC — Sketch Operations (VTK-compatible Edition, fixed Render)
Author: AlumProCNC Team

نسخة تعمل بالكامل بدون OCC DisplayShape — متوافقة مع VTKViewer.
تم تصحيح renderWindow ليعمل عبر vtk_widget.GetRenderWindow().
"""

from typing import List, Tuple, Optional
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCC.Core.GC import GC_MakeLine, GC_MakeCircle, GC_MakeArcOfCircle, GC_MakeEllipse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

ColorTuple = Tuple[float, float, float]
Point3D = Tuple[float, float, float]

def _qcolor(rgb: ColorTuple) -> Quantity_Color:
    r, g, b = rgb
    return Quantity_Color(r, g, b, Quantity_TOC_RGB)

def _debug(msg: str):
    print(f"[SKETCH] {msg}")

class SketchOps:
    def __init__(self, display, default_color: ColorTuple = (0.15, 0.25, 0.45), line_width: float = 1.5):
        self.display = display
        self.default_color = default_color
        self.line_width = line_width

        # كشف نوع العارض (OCC أو VTK)
        if hasattr(display, "GetContext"):
            self.ctx = display.GetContext()
            self.viewer_type = "OCC"
            _debug("Linked to OCC Display Context ✅")
        else:
            self.ctx = None
            self.viewer_type = "VTK"
            _debug("Linked to VTKViewer (no OCC context) ⚙️")

    # -----------------------------------------------------
    # عرض الشكل
    # -----------------------------------------------------
    def _show(self, shape, color: Optional[ColorTuple] = None, update: bool = True):
        if self.viewer_type == "VTK":
            import vtk
            if color is None:
                color = self.default_color
            try:
                actor = vtk.vtkActor()
                actor.GetProperty().SetColor(*color)
                actor.GetProperty().SetLineWidth(self.line_width)
                self.display.renderer.AddActor(actor)
                self.display.vtk_widget.GetRenderWindow().Render()
                _debug("[VTK] Shape displayed (placeholder actor)")
            except Exception as e:
                _debug(f"[VTK] ⚠️ Failed to show shape: {e}")
            return None

        # الوضع الأصلي (OCC)
        ais = self.display.DisplayShape(shape, update=update)
        if color is None:
            color = self.default_color
        self.ctx.SetColor(ais, _qcolor(color))
        try:
            self.ctx.SetWidth(ais, self.line_width)
        except Exception:
            pass
        return ais

    # -----------------------------------------------------
    # أدوات الرسم
    # -----------------------------------------------------
    def line(self, p1: Point3D, p2: Point3D, color: Optional[ColorTuple] = None):
        _debug(f"Line {p1}->{p2}")
        if self.viewer_type == "VTK":
            _debug("[VTK] رسم خط")
            import vtk
            line = vtk.vtkLineSource()
            line.SetPoint1(*p1)
            line.SetPoint2(*p2)
            line.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(line.GetOutput())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*(color or self.default_color))
            actor.GetProperty().SetLineWidth(self.line_width)
            self.display.renderer.AddActor(actor)
            self.display.vtk_widget.GetRenderWindow().Render()
            return None

        edge = BRepBuilderAPI_MakeEdge(GC_MakeLine(gp_Pnt(*p1), gp_Pnt(*p2)).Value()).Edge()
        self._show(edge, color)
        return edge

    def circle(self, center: Point3D, radius: float, color: Optional[ColorTuple] = None):
        _debug(f"Circle center={center}, r={radius}")
        if self.viewer_type == "VTK":
            _debug("[VTK] رسم دائرة")
            import vtk
            circ = vtk.vtkRegularPolygonSource()
            circ.SetCenter(*center)
            circ.SetRadius(float(radius))
            circ.SetNumberOfSides(64)
            circ.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(circ.GetOutput())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*(color or self.default_color))
            actor.GetProperty().SetLineWidth(self.line_width)
            actor.GetProperty().SetRepresentationToWireframe()
            self.display.renderer.AddActor(actor)
            self.display.vtk_widget.GetRenderWindow().Render()
            return None

        try:
            ax2 = gp_Ax2(gp_Pnt(*center), gp_Dir(0, 0, 1))
            circ = GC_MakeCircle(ax2, float(radius)).Value()
            edge = BRepBuilderAPI_MakeEdge(circ).Edge()
            self._show(edge, color)
            return edge
        except Exception as e:
            _debug(f"❌ [Circle] خطأ: {e}")
            return None

    def rectangle(self, origin: Point3D, width: float, height: float, color: Optional[ColorTuple] = None):
        _debug(f"Rect origin={origin}, w={width}, h={height}")
        if self.viewer_type == "VTK":
            import vtk
            x, y, z = origin
            pts = [(x, y, z), (x+width, y, z), (x+width, y+height, z), (x, y+height, z)]
            poly = vtk.vtkPolygon()
            poly.GetPointIds().SetNumberOfIds(4)
            points = vtk.vtkPoints()
            for i, p in enumerate(pts):
                points.InsertNextPoint(*p)
                poly.GetPointIds().SetId(i, i)
            cells = vtk.vtkCellArray()
            cells.InsertNextCell(poly)
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(cells)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*(color or self.default_color))
            actor.GetProperty().SetRepresentationToWireframe()
            self.display.renderer.AddActor(actor)
            self.display.vtk_widget.GetRenderWindow().Render()
            _debug("[VTK] رسم مستطيل")
            return None

        x, y, z = origin
        pts = [gp_Pnt(x, y, z), gp_Pnt(x+width, y, z), gp_Pnt(x+width, y+height, z), gp_Pnt(x, y+height, z), gp_Pnt(x, y, z)]
        wmk = BRepBuilderAPI_MakeWire()
        for i in range(4):
            wmk.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[i+1]).Edge())
        wire = wmk.Wire()
        self._show(wire, color)
        return wire

    def arc_3pt(self, p1: Point3D, p2: Point3D, p3: Point3D, color: Optional[ColorTuple] = None):
        _debug(f"Arc3pt {p1},{p2},{p3}")
        if self.viewer_type == "VTK":
            import vtk
            arc = vtk.vtkArcSource()
            arc.SetPoint1(*p1)
            arc.SetPoint2(*p3)
            arc.SetCenter(*p2)
            arc.SetResolution(64)
            arc.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(arc.GetOutput())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*(color or self.default_color))
            actor.GetProperty().SetLineWidth(self.line_width)
            self.display.renderer.AddActor(actor)
            self.display.vtk_widget.GetRenderWindow().Render()
            _debug("[VTK] رسم قوس")
            return None

        edge = BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(gp_Pnt(*p1), gp_Pnt(*p2), gp_Pnt(*p3)).Value()).Edge()
        self._show(edge, color)
        return edge
