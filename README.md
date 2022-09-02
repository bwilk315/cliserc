# Bartek's Notation
### Description
This simple and small module is capable of serializing any data into easy-to-maintain
key-value pairs. Use it when there is need to serialize data in order to send it through
some sort of transmission medium which accepts bytes as only type of data you can send.
It is obvious that later the data received needs to be deserialized and then used.
The syntax of data serialized is very simple and if you are a good programmer you should
be able to create a decoder in all languages you already know.
### Syntax
##### Structure
As mentioned above, the syntax is ultimately simple:
- Key and value are separated by colon symbol (:)
- Value is enclosed in single quotes (')
- Each key-value pair is preceded by semicolon symbol (';')
##### Example
Result of serializing a dictionary with keys:
- x equal 12 and
- msg equal _Bartek's_
```
x:'12';y:'Bartek\'s';
```
Note that:
- Apostrophe is automatically escaped
- Last key-value pair has semicolon included too
### Documentation
_BNot_ class is used for de/serialization management. It contains few methods:
- **\_\_init\_\_**\
Initializes the 'BNot' class instance for managing Bartek's Notation
  - data: Starting dictionary of variables
- **\_\_str\_\_**\
Returns string representation of class instance, here it is the dictionary of variables (as string)
- **decode**\
Converts data encoded to Bartek's Notation into dictionary (of variables encoded earlier)
Note that variable values will be converted to possible type in following order: int > float > string,
it means: convert to int, then if failed to float, and if this failed too, then to string
  - code: Text encoded to Bartek's Notation format
- **var**\
Defines a new value of variable named 'name' with value 'value' assigned to it
  - name: Name of the variable to set
  - value: New value of variable with name specified
- **get**\
Returns the value of variable named 'name', if it does not exist 'default' value is returned
  - name: Name of variable you want to access
  - default: Value returned if variable is not found
- **und**\
Undefines (deletes) the variable with given name
  - name:    Name of the variable to delete/undefine
- **encode**\
Converts dictionary (of variables) into Bartek's Notation (text format), exports encoded data into
text file under path 'file' if this feature is enabled
  - export:  If enabled, encoded data will be exported to a file
  - file:    Path to the file which will be wrote with encoded data, works only if 'export' is enabled
