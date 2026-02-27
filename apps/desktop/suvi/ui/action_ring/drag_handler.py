from PyQt6.QtCore import QObject, QEvent, Qt, QPoint, pyqtSignal

class DragHandler(QObject):
    # This signal fires only if the user taps the ring without dragging it
    clicked = pyqtSignal() 

    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        # Attach the filter so we can intercept mouse events
        self.widget.installEventFilter(self)
        
        self._drag_start_pos = None
        self._is_dragging = False

    def eventFilter(self, obj, event):
        if obj is self.widget:
            # 1. Mouse Press: Record starting position
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_pos = event.globalPosition().toPoint() - self.widget.frameGeometry().topLeft()
                self._is_dragging = False
                return True # Event intercepted and handled

            # 2. Mouse Move: Move the window if holding left click
            elif event.type() == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
                if self._drag_start_pos is not None:
                    current_pos = event.globalPosition().toPoint()
                    new_pos = current_pos - self._drag_start_pos
                    
                    # If moved more than 5 pixels, it's officially a drag
                    if not self._is_dragging and (current_pos - (self.widget.frameGeometry().topLeft() + self._drag_start_pos)).manhattanLength() > 5:
                        self._is_dragging = True
                        
                    if self._is_dragging:
                        self.widget.move(new_pos)
                    return True

            # 3. Mouse Release: Decide if it was a drag or a click
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if self._drag_start_pos is not None:
                    if not self._is_dragging:
                        # It was a tap! Tell the window to animate.
                        self.clicked.emit() 
                    else:
                        print(f"Ring repositioned to: {self.widget.pos().x()}, {self.widget.pos().y()}")
                        # TODO: Emit async event to save new coordinates to Firestore Profile
                        
                    self._drag_start_pos = None
                    self._is_dragging = False
                return True

        return super().eventFilter(obj, event)