import javalang
import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.jade.java_parser import parse_impacted_objects_and_methods, extract_impacted_lines

# Updated sample Java code with fields and constructors
sample_java_code = """
public class MyClass {
    private String field1;
    private int field2;

    public MyClass() {
        this.field1 = "initialized";
    }

    public void method1() {
        field1 = "updated";
    }

    public void method2() {
        System.out.println(field2);
    }
}
"""

# Updated Git diff output
sample_diff_output = """
diff --git a/MyClass.java b/MyClass.java
index 12345..67890 100644
--- a/MyClass.java
+++ b/MyClass.java
@@ -2,0 +3,2 @@ public class MyClass {
+    private String field1;
@@ -5,0 +6,2 @@ public MyClass() {
+    this.field1 = "initialized";
    }
"""

# Sample affected files
mock_affected_files = ["MyClass.java"]


@pytest.fixture
def mock_javalang():
    """Fixture to mock javalang parsing and create a mocked AST tree"""

    class MockStatement:
        """Mock statement to simulate MemberReference or Assignment behavior."""

        def __init__(self, field_name):
            self.member = field_name

    class MockMethodDeclaration:
        def __init__(self, name, constructor, start, end, body=None):
            self.name = name
            self.constructor = constructor
            self.position = MockPosition(start)
            self.body = body if body else []

    class MockPosition:
        def __init__(self, line):
            self.line = line

    class MockFieldDeclaration:
        def __init__(self, names, start, end):
            class MockDeclarator:
                def __init__(self, name):
                    self.name = name

            self.position = MockPosition(start)
            self.declarators = [MockDeclarator(name) for name in names]

    mock_tree = MagicMock()
    mock_tree.filter.side_effect = lambda node_type: {
        javalang.tree.MethodDeclaration: [
            ("constructor_path", MockMethodDeclaration("MyClass", True, 6, 8)),
            ("method1_path", MockMethodDeclaration("method1", False, 10, 12, [MockStatement("field1")])),
            ("method2_path", MockMethodDeclaration("method2", False, 14, 16))
        ],
        javalang.tree.FieldDeclaration: [
            ("field1_path", MockFieldDeclaration(["field1"], 3, 3)),
            ("field2_path", MockFieldDeclaration(["field2"], 4, 4))
        ]
    }.get(node_type, [])

    return mock_tree


def test_parse_impacted_objects_and_methods(mock_javalang, monkeypatch):
    """Test the enhanced `parse_impacted_objects_and_methods` function"""
    monkeypatch.setattr("builtins.open", mock_open(read_data=sample_java_code))
    monkeypatch.setattr("javalang.parse.parse", lambda x: mock_javalang)

    impacted = parse_impacted_objects_and_methods(sample_diff_output, mock_affected_files)

    # The test should check for all the new fields we've added
    assert "impacted_methods" in impacted["MyClass.java"]
    assert "impacted_constructors" in impacted["MyClass.java"]
    assert "impacted_fields" in impacted["MyClass.java"]
    assert "impacted_classes" in impacted["MyClass.java"]
    assert "impacted_annotations" in impacted["MyClass.java"]
    assert "impacted_static_blocks" in impacted["MyClass.java"]
    assert "impacted_instance_blocks" in impacted["MyClass.java"]
    assert "impacted_exceptions" in impacted["MyClass.java"]

    # Check specific values for the fields we know should be impacted
    assert impacted["MyClass.java"]["impacted_methods"] == ["method1"]
    assert impacted["MyClass.java"]["impacted_constructors"] == ["MyClass"]
    assert impacted["MyClass.java"]["impacted_fields"] == {
        "field1": "high",  # Referenced in method1
        "field2": "low"  # Not referenced
    }
