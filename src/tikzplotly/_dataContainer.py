import re
from ._utils import replace_all_digits, sanitize_text
from ._data import treat_data, post_treat_data

def hexid_to_alpha(num):
    hexstr = str(num)
    table = "ABCDEFGHIJKLMNOP"
    return ''.join(table[int(c, 16)] for c in hexstr if c in "0123456789abcdef")

class Data:

    def __init__(self, name, x):
        """Initialize a Data object.

        Parameters
        ----------
        name
            name of the data
        x
            x_values of the data
        """
        self.name = name
        self.macro_name = "\\" + replace_all_digits(name)
        self.x = x
        self.y_label = []
        self.y_data = []

    def addYData(self, y, y_label=None):
        if y_label is not None and len(y_label) > 0:
            y_label = y_label.replace(" ", "_")
            self.y_label.append(y_label)
        else:
            self.y_label.append(f"y{len(self.y_label)}")
        self.y_data.append(y)
        return self.y_label[-1]

class Data3D:
    def __init__(self, x, y, z, name):
        self.x = list(x)
        self.y = list(y)
        self.z = list(z)
        self.name = name if name else f"data{hexid_to_alpha(id(self))}"
        self.z_name = "z"

class DataContainer:

    def __init__(self):
        self.data = []

    def addData(self, x, y, name=None, y_label=None):
        """Add data to the container.

        Parameters
        ----------
        x
            x values of the data
        y
            y values of the data
        y_label, optional
            name of the y data, by default None
        name, optional
            name of the data, by default None

        Returns
        -------
            tuple (macro_name, y_label), where macro_name is the name of the data in LaTeX and y_label the name of the y data in LaTeX
        """
        for data in self.data:
            if isinstance(x, (tuple, list)):
                continue
            if len(data.x) != len(x):
                continue
            are_equals = data.x == x
            if type(are_equals) == bool:
                if are_equals:
                    y_label_val = data.addYData(y, y_label or name)
                    return data.macro_name, y_label_val
            elif hasattr(are_equals, "all") and are_equals.all():
                y_label_val = data.addYData(y, y_label or name)
                return data.macro_name, y_label_val
        data_to_add = Data(f"data{len(self.data)}", x)
        y_label_val = data_to_add.addYData(y, y_label or name)
        self.data.append(data_to_add)
        return data_to_add.macro_name, sanitize_text(y_label_val)

    def addData3D(self, x, y, z, name=None):
        """Add data to the container.

        Parameters
        ----------
        x
            x values of the data
        y
            y values of the data
        z
            z values of the data
        name, optional
            name of the data, by default None

        Returns
        -------
            tuple (macro_name, z_name), where macro_name is the name of the data in LaTeX and z_name the name of the z data in LaTeX
        """
        for data in self.data:
            if hasattr(data, "x") and hasattr(data, "y") and hasattr(data, "z"):
                import numpy as np
                if np.array_equal(data.x, x) and np.array_equal(data.y, y) and np.array_equal(data.z, z):
                    return data.name, data.z_name
        data_obj = Data3D(x, y, z, name)
        self.data.append(data_obj)
        return data_obj.name, data_obj.z_name

    def exportData(self):
        """Generate LaTeX code to export the data from DataContainer.

        Returns
        -------
            string of LaTeX code
        """
        export_string = ""

        for data in self.data:
            # 3D
            if hasattr(data, "z"):
                export_string += "\\pgfplotstableread{\n"
                export_string += "x y z\n"
                for i in range(len(data.x)):
                    export_string += f"{data.x[i]} {data.y[i]} {data.z[i]}\n"
                export_string += f"}}{{\\{data.name}}}\n"
            
            # 2D 
            else:
                export_string += "\\pgfplotstableread{\n"
                header = "x"
                if hasattr(data, "y_label") and data.y_label:
                    for label in data.y_label:
                        header += f" {label}"
                else:
                    header += " y"
                export_string += header + "\n"
                for i in range(len(data.x)):
                    row = [str(data.x[i])]
                    for y_col in data.y_data:
                        row.append(str(y_col[i]))
                    export_string += " ".join(row) + "\n"
                export_string += f"}}\\{data.name}\n"

        return post_treat_data(export_string)

