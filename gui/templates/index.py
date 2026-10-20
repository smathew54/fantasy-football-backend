<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Items</title>
</head>
<body>
    <h1>Items List</h1>
    <ul>
        {% for item in items %}
            <li>{{ item.name }}</li>
        {% endfor %}
    </ul>
</body>
</html>
