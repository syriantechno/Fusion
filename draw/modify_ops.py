# Fusion/draw/modify_ops.py
# -*- coding: utf-8 -*-
import math
import vtk

class ModifyOps:
    """أدوات التعديل: Trim / Offset / Mirror / Fillet"""
    def __init__(self, viewer):
        self.viewer = viewer
        self.renderer = viewer.renderer

    # ✂️ Trim: يحذف أقرب عنصر للنقرة (نسخة أولية — نطوّرها لاحقًا)
    def trim(self, click_world):
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        closest, best = None, float("inf")
        a = actors.GetNextActor()
        while a:
            try:
                b = a.GetBounds()
                cx, cy = (b[0]+b[1])/2.0, (b[2]+b[3])/2.0
                d = math.hypot(click_world[0]-cx, click_world[1]-cy)
                if d < best:
                    best, closest = d, a
            except:
                pass
            a = actors.GetNextActor()
        if closest and best < 20:
            self.renderer.RemoveActor(closest)
            self.renderer.GetRenderWindow().Render()

    # ↔ Offset: ينسخ العنصر بإزاحة بسيطة (مبدئيًا ترجمة)
    def offset(self, base_actor, distance=10.0):
        if not base_actor: return
        tf = vtk.vtkTransform(); tf.Translate(distance, distance, 0)
        filt = vtk.vtkTransformPolyDataFilter()
        filt.SetInputData(base_actor.GetMapper().GetInput())
        filt.SetTransform(tf); filt.Update()
        m = vtk.vtkPolyDataMapper(); m.SetInputData(filt.GetOutput())
        n = vtk.vtkActor(); n.SetMapper(m)
        n.GetProperty().SetColor(0.45, 0.55, 0.8)
        self.renderer.AddActor(n)
        self.renderer.GetRenderWindow().Render()

    # 🔁 Mirror: مرآة حول محور X أو Y (مبدئيًا)
    def mirror(self, base_actor, axis="Y"):
        if not base_actor: return
        s = (1, -1, 1) if axis.upper()=="X" else (-1, 1, 1)
        tf = vtk.vtkTransform(); tf.Scale(*s)
        filt = vtk.vtkTransformPolyDataFilter()
        filt.SetInputData(base_actor.GetMapper().GetInput())
        filt.SetTransform(tf); filt.Update()
        m = vtk.vtkPolyDataMapper(); m.SetInputData(filt.GetOutput())
        n = vtk.vtkActor(); n.SetMapper(m)
        n.GetProperty().SetColor(0.5, 0.5, 0.7)
        self.renderer.AddActor(n)
        self.renderer.GetRenderWindow().Render()

    # ◔ Fillet: قوس بسيط بين نقطتين (نسخة أولية — نطورها لاحقًا)
    def fillet(self, p1, p2, radius=5.0):
        arc = vtk.vtkArcSource()
        arc.SetPoint1(*p1); arc.SetPoint2(*p2)
        arc.SetCenter((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0, 0.0)
        arc.SetResolution(64); arc.Update()
        m = vtk.vtkPolyDataMapper(); m.SetInputConnection(arc.GetOutputPort())
        a = vtk.vtkActor(); a.SetMapper(m)
        a.GetProperty().SetColor(0.6, 0.5, 0.8)
        a.GetProperty().SetLineWidth(2)
        self.renderer.AddActor(a)
        self.renderer.GetRenderWindow().Render()
