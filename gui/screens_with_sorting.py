"""
GUI screens with sorting functionality for Mobile Shop Manager.
Includes InventoryScreen with column sorting capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SortDirection(Enum):
    """Enumeration for sort direction."""
    ASCENDING = "ascending"
    DESCENDING = "descending"


@dataclass
class SortState:
    """Data class to track sorting state."""
    column: Optional[str] = None
    direction: SortDirection = SortDirection.ASCENDING


class InventoryScreen(ttk.Frame):
    """
    Screen for displaying and managing mobile phone inventory with column sorting.
    
    Features:
    - Display inventory items in a table format
    - Sort by clicking column headers
    - Support for IMEI, Model, Price, Supplier, Status columns
    - Filter and search functionality
    - Visual indicators for sort direction
    """

    # Column definitions
    COLUMNS = {
        "IMEI": {"width": 150, "anchor": "w"},
        "Model": {"width": 150, "anchor": "w"},
        "Price": {"width": 100, "anchor": "e"},
        "Supplier": {"width": 120, "anchor": "w"},
        "Status": {"width": 100, "anchor": "center"},
        "Quantity": {"width": 80, "anchor": "center"},
        "Date Added": {"width": 120, "anchor": "center"},
    }

    SORT_INDICATORS = {
        SortDirection.ASCENDING: " ▲",
        SortDirection.DESCENDING: " ▼",
    }

    def __init__(self, parent, data_source: Optional[Callable] = None, **kwargs):
        """
        Initialize the InventoryScreen.
        
        Args:
            parent: Parent widget
            data_source: Callable that returns inventory data
            **kwargs: Additional keyword arguments for ttk.Frame
        """
        super().__init__(parent, **kwargs)
        
        self.data_source = data_source
        self.sort_state = SortState()
        self.filtered_data: List[Dict[str, Any]] = []
        self.all_data: List[Dict[str, Any]] = []
        
        # UI Components
        self.tree: Optional[ttk.Treeview] = None
        self.search_var: Optional[tk.StringVar] = None
        self.status_var: Optional[tk.StringVar] = None
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create toolbar frame
        toolbar_frame = ttk.LabelFrame(main_frame, text="Filters & Search", padding=5)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search field
        search_label = ttk.Label(toolbar_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Status filter
        status_label = ttk.Label(toolbar_frame, text="Status:")
        status_label.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar()
        self.status_var.trace("w", self._on_filter_change)
        status_combo = ttk.Combobox(
            toolbar_frame,
            textvariable=self.status_var,
            values=["All", "Active", "Inactive", "Sold", "Pending"],
            state="readonly",
            width=15
        )
        status_combo.set("All")
        status_combo.pack(side=tk.LEFT, padx=5)

        # Reset button
        reset_button = ttk.Button(toolbar_frame, text="Reset Sorting", command=self._reset_sorting)
        reset_button.pack(side=tk.RIGHT, padx=5)

        # Create tree frame with scrollbars
        tree_frame = ttk.LabelFrame(main_frame, text="Inventory", padding=5)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        # Create Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=tuple(self.COLUMNS.keys()),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=20
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Configure columns
        for column, config in self.COLUMNS.items():
            self.tree.heading(column, text=column, command=lambda c=column: self._on_tree_click(c))
            self.tree.column(column, width=config["width"], anchor=config["anchor"])

        # Pack tree and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Configure tree style
        self.tree.bind("<Button-1>", self._on_tree_button_click)

        # Status bar frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(status_frame, text="Items displayed:", relief=tk.SUNKEN).pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="0", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, padx=5)

    def load_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Load data into the inventory screen.
        
        Args:
            data: List of inventory items (dictionaries with column keys)
        """
        self.all_data = data.copy()
        self._apply_filters()

    def _on_search_change(self, *args) -> None:
        """Handle search field changes."""
        self._apply_filters()

    def _on_filter_change(self, *args) -> None:
        """Handle filter changes."""
        self._apply_filters()

    def _on_tree_button_click(self, event) -> None:
        """
        Handle tree view button clicks to detect column header clicks.
        
        Args:
            event: Tkinter event object
        """
        if not self.tree:
            return

        # Get the region that was clicked
        region = self.tree.identify_region(event.x, event.y)
        
        # Only process heading region clicks
        if region != "heading":
            return

        column = self.tree.identify_column(event.x)
        col_index = int(column) - 1
        
        if 0 <= col_index < len(self.COLUMNS):
            column_name = list(self.COLUMNS.keys())[col_index]
            self._on_tree_click(column_name)

    def _on_tree_click(self, column: str) -> None:
        """
        Handle column header click for sorting.
        
        Args:
            column: Name of the column that was clicked
        """
        # Toggle sort direction if clicking the same column
        if self.sort_state.column == column:
            if self.sort_state.direction == SortDirection.ASCENDING:
                self.sort_state.direction = SortDirection.DESCENDING
            else:
                self.sort_state.direction = SortDirection.ASCENDING
        else:
            # New column selected, start with ascending
            self.sort_state.column = column
            self.sort_state.direction = SortDirection.ASCENDING

        self._apply_filters()

    def _sort_by_column(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort data by the current sort state.
        
        Args:
            data: List of items to sort
            
        Returns:
            Sorted list of items
        """
        if not self.sort_state.column or not data:
            return data

        column = self.sort_state.column
        reverse = self.sort_state.direction == SortDirection.DESCENDING

        # Determine sort key function based on column type
        def sort_key(item):
            value = item.get(column, "")
            
            # Handle different data types
            if column in ["Price", "Quantity"]:
                try:
                    return float(str(value).replace("$", "").replace(",", ""))
                except (ValueError, AttributeError):
                    return 0
            
            # String columns
            if isinstance(value, str):
                return value.lower()
            
            return value

        sorted_data = sorted(data, key=sort_key, reverse=reverse)
        return sorted_data

    def _apply_filters(self) -> None:
        """Apply search and filter criteria, then render the tree."""
        filtered_data = self.all_data.copy()

        # Apply search filter
        search_term = (self.search_var.get() if self.search_var else "").lower()
        if search_term:
            filtered_data = [
                item for item in filtered_data
                if any(
                    search_term in str(item.get(col, "")).lower()
                    for col in self.COLUMNS.keys()
                )
            ]

        # Apply status filter
        status_filter = self.status_var.get() if self.status_var else "All"
        if status_filter != "All":
            filtered_data = [
                item for item in filtered_data
                if item.get("Status", "").lower() == status_filter.lower()
            ]

        # Apply sorting
        self.filtered_data = self._sort_by_column(filtered_data)

        # Render the tree
        self._render_tree()

    def _render_tree(self) -> None:
        """Render the tree view with filtered and sorted data."""
        if not self.tree:
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Update column headers with sort indicators
        self._update_column_headers()

        # Insert filtered data
        for item_data in self.filtered_data:
            values = [item_data.get(col, "") for col in self.COLUMNS.keys()]
            self.tree.insert("", "end", values=values)

        # Update status label
        if self.status_label:
            self.status_label.config(text=str(len(self.filtered_data)))

    def _update_column_headers(self) -> None:
        """Update column headers to show sort direction indicator."""
        if not self.tree:
            return

        for idx, column in enumerate(self.COLUMNS.keys()):
            header_text = column
            
            # Add sort indicator if this is the sorted column
            if self.sort_state.column == column:
                indicator = self.SORT_INDICATORS[self.sort_state.direction]
                header_text = f"{column}{indicator}"
            
            self.tree.heading(idx, text=header_text)

    def _reset_sorting(self) -> None:
        """Reset sorting to default state."""
        self.sort_state = SortState()
        self._apply_filters()

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected item.
        
        Returns:
            Dictionary of the selected item or None
        """
        if not self.tree:
            return None

        selection = self.tree.selection()
        if not selection:
            return None

        # Get the selected item's values
        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        
        # Map values back to dictionary
        item_dict = {
            col: val for col, val in zip(self.COLUMNS.keys(), values)
        }
        
        return item_dict

    def get_all_visible_items(self) -> List[Dict[str, Any]]:
        """
        Get all visible (filtered) items.
        
        Returns:
            List of visible items as dictionaries
        """
        return self.filtered_data.copy()

    def refresh_data(self) -> None:
        """Refresh data from the data source if available."""
        if self.data_source:
            data = self.data_source()
            self.load_data(data)

    def add_item(self, item: Dict[str, Any]) -> None:
        """
        Add a new item to the inventory.
        
        Args:
            item: Dictionary containing item data
        """
        self.all_data.append(item)
        self._apply_filters()

    def update_item(self, imei: str, item: Dict[str, Any]) -> None:
        """
        Update an existing item by IMEI.
        
        Args:
            imei: IMEI number of the item to update
            item: Updated item data
        """
        for i, existing_item in enumerate(self.all_data):
            if existing_item.get("IMEI") == imei:
                self.all_data[i] = item
                break
        self._apply_filters()

    def delete_item(self, imei: str) -> None:
        """
        Delete an item by IMEI.
        
        Args:
            imei: IMEI number of the item to delete
        """
        self.all_data = [
            item for item in self.all_data
            if item.get("IMEI") != imei
        ]
        self._apply_filters()

    def clear_data(self) -> None:
        """Clear all data from the inventory."""
        self.all_data.clear()
        self.filtered_data.clear()
        self.sort_state = SortState()
        self._render_tree()


class SortableDataGrid(InventoryScreen):
    """
    Extended InventoryScreen with additional data grid features.
    Can be used as a generic sortable data grid for any tabular data.
    """

    def __init__(self, parent, columns: Optional[Dict[str, Dict]] = None, **kwargs):
        """
        Initialize the SortableDataGrid.
        
        Args:
            parent: Parent widget
            columns: Dictionary of column definitions (name: {width, anchor})
            **kwargs: Additional keyword arguments
        """
        if columns:
            # Override class COLUMNS with provided columns
            self.COLUMNS = columns
        
        super().__init__(parent, **kwargs)

    def configure_columns(self, columns: Dict[str, Dict]) -> None:
        """
        Configure grid columns.
        
        Args:
            columns: Dictionary of column definitions
        """
        self.COLUMNS = columns
        # Rebuild the UI with new columns
        for widget in self.winfo_children():
            widget.destroy()
        self._setup_ui()


# Example usage and test data
if __name__ == "__main__":
    
    root = tk.Tk()
    root.title("Mobile Shop Manager - Inventory")
    root.geometry("1200x600")

    # Sample data
    sample_data = [
        {
            "IMEI": "123456789012345",
            "Model": "iPhone 14",
            "Price": "$899",
            "Supplier": "Apple",
            "Status": "Active",
            "Quantity": "5",
            "Date Added": "2026-01-10"
        },
        {
            "IMEI": "123456789012346",
            "Model": "Samsung S24",
            "Price": "$799",
            "Supplier": "Samsung",
            "Status": "Active",
            "Quantity": "3",
            "Date Added": "2026-01-11"
        },
        {
            "IMEI": "123456789012347",
            "Model": "Pixel 8",
            "Price": "$699",
            "Supplier": "Google",
            "Status": "Pending",
            "Quantity": "2",
            "Date Added": "2026-01-12"
        },
        {
            "IMEI": "123456789012348",
            "Model": "OnePlus 12",
            "Price": "$649",
            "Supplier": "OnePlus",
            "Status": "Active",
            "Quantity": "4",
            "Date Added": "2026-01-09"
        },
        {
            "IMEI": "123456789012349",
            "Model": "Xiaomi 14",
            "Price": "$599",
            "Supplier": "Xiaomi",
            "Status": "Inactive",
            "Quantity": "1",
            "Date Added": "2026-01-08"
        },
    ]

    # Create and load inventory screen
    inventory_screen = InventoryScreen(root)
    inventory_screen.pack(fill=tk.BOTH, expand=True)
    inventory_screen.load_data(sample_data)

    root.mainloop()
