# -*- coding: utf-8 -*-
"""
grid_axes_manager.py
نسخة مستقرة وخفيفة (من كودك القديم)
"""

import vtk


class GridAxesManager:
    def __init__(self, renderer):
        self.renderer = renderer
        self._create_grid()
        self._create_axes()

    # ------------------------------------------------------------------
    # شبكة خفيفة جداً (خطوط بسيطة XY)
    # ------------------------------------------------------------------
    def _create_grid(self):
        grid_size = 10
        spacing = 10.0

        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()

        # خطوط على محور X
        for i in range(-grid_size, grid_size + 1):
            p1 = (i * spacing, -grid_size * spacing, 0.0)
            p2 = (i * spacing, grid_size * spacing, 0.0)
            id1 = points.InsertNextPoint(*p1)
            id2 = points.InsertNextPoint(*p2)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, id1)
            line.GetPointIds().SetId(1, id2)
            lines.InsertNextCell(line)

        # خطوط على محور Y
        for j in range(-grid_size, grid_size + 1):
            p1 = (-grid_size * spacing, j * spacing, 0.0)
            p2 = (grid_size * spacing, j * spacing, 0.0)
            id1 = points.InsertNextPoint(*p1)
            id2 = points.InsertNextPoint(*p2)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, id1)
            line.GetPointIds().SetId(1, id2)
            lines.InsertNextCell(line)

        grid_poly = vtk.vtkPolyData()
        grid_poly.SetPoints(points)
        grid_poly.SetLines(lines)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(grid_poly)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.7, 0.7, 0.7)
        actor.GetProperty().SetLineWidth(1)
        actor.GetProperty().SetOpacity(0.6)

        self.renderer.AddActor(actor)

    # ------------------------------------------------------------------
    # محاور أساسية (X Y Z)
    # ------------------------------------------------------------------
    def _create_axes(self):
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(50, 50, 50)
        axes.AxisLabelsOn()
        self.renderer.AddActor(axes)
