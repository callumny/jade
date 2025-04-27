import javalang

def parse_impacted_objects_and_methods(diff_output: str, affected_files: list[str]) -> dict[str, dict]:
    """
    Parse the impacted objects, methods, constructors, and field declarations from the diff output.

    Args:
        diff_output (str): The raw diff output from `get_git_diff`.
        affected_files (list): List of files affected (output of `get_affected_files`).

    Returns:
        dict: Dictionary where keys are files and values are:
              {
                  "impacted_methods": [list of impacted method names],
                  "impacted_constructors": [list of impacted constructors],
                  "impacted_fields": {
                      "field_name": "high" | "low" (impact level based on method references)
                  },
                  "impacted_classes": {
                      "class_name": {
                          "type": "new" | "deleted" | "modified",
                          "inheritance_changed": True | False,
                          "modifiers_changed": True | False
                      }
                  },
                  "impacted_annotations": [list of impacted annotations],
                  "impacted_static_blocks": [list of impacted static blocks],
                  "impacted_instance_blocks": [list of impacted instance blocks],
                  "impacted_exceptions": [list of impacted exceptions]
              }
    """
    impacted = {}

    for file in affected_files:
        try:
            # Get impacted lines from diff
            impacted_lines = extract_impacted_lines(diff_output, file)

            # Parse Java file using javalang
            with open(file, 'r') as f:
                java_code = f.read()

            tree = javalang.parse.parse(java_code)

            impacted_data = {
                "impacted_methods": [],
                "impacted_constructors": [],
                "impacted_fields": {},
                "impacted_classes": {},
                "impacted_annotations": [],
                "impacted_static_blocks": [],
                "impacted_instance_blocks": [],
                "impacted_exceptions": []
            }

            # Find all field declarations
            field_references = {}
            for _, field_node in tree.filter(javalang.tree.FieldDeclaration):
                field_start_line = field_node.position.line
                field_end_line = getattr(
                    field_node.declarators[-1], "position", field_node.position
                ).line  # Consider all field declarators
                field_names = [decl.name for decl in field_node.declarators]

                # Check if this field has impacted lines
                if any(field_start_line <= line <= field_end_line for line in impacted_lines):
                    for field in field_names:
                        field_references[field] = {
                            "impact": "low",  # Default to "low" impact
                            "referenced": False
                        }

            # Find impacted methods and constructors
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                node_start_line = node.position.line
                node_end_line = getattr(node.body[-1], "position", node.position).line if node.body else node.position.line

                # Check if method signature is impacted
                signature_impacted = any(node_start_line == line for line in impacted_lines)

                # Check if method body is impacted
                body_impacted = any(node_start_line < line <= node_end_line for line in impacted_lines)

                # Check if method references any impacted fields
                references_impacted_field = False
                for field in field_references.keys():
                    if is_field_referenced(field, node.body):
                        field_references[field]["referenced"] = True
                        references_impacted_field = True

                if signature_impacted or body_impacted or references_impacted_field:
                    if node.constructor:
                        impacted_data["impacted_constructors"].append(node.name)
                    else:
                        impacted_data["impacted_methods"].append(node.name)

                    # Check for exceptions in method signature
                    if hasattr(node, 'throws') and node.throws and signature_impacted:
                        for exception in node.throws:
                            exception_name = exception.name if hasattr(exception, 'name') else str(exception)
                            if exception_name not in impacted_data["impacted_exceptions"]:
                                impacted_data["impacted_exceptions"].append(exception_name)

            # Find impacted classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                class_start_line = node.position.line
                class_end_line = max([getattr(item, "position", node.position).line 
                                    for item in node.body]) if node.body else node.position.line

                # Check if class is impacted
                if any(class_start_line <= line <= class_end_line for line in impacted_lines):
                    class_info = {
                        "type": "modified",  # Default to modified
                        "inheritance_changed": False,
                        "modifiers_changed": False
                    }

                    # Check if class declaration line is impacted (for inheritance or modifiers)
                    if any(class_start_line == line for line in impacted_lines):
                        # Check for inheritance changes
                        if hasattr(node, 'extends') and node.extends:
                            class_info["inheritance_changed"] = True

                        # Check for implements changes
                        if hasattr(node, 'implements') and node.implements:
                            class_info["inheritance_changed"] = True

                        # Check for modifier changes
                        if hasattr(node, 'modifiers') and node.modifiers:
                            class_info["modifiers_changed"] = True

                    impacted_data["impacted_classes"][node.name] = class_info

            # Find impacted annotations
            for path, node in tree.filter(javalang.tree.Annotation):
                if hasattr(node, 'position') and node.position:
                    annotation_line = node.position.line
                    if annotation_line in impacted_lines:
                        annotation_name = node.name if hasattr(node, 'name') else str(node)
                        if annotation_name not in impacted_data["impacted_annotations"]:
                            impacted_data["impacted_annotations"].append(annotation_name)

            # Find impacted initializer blocks
            for path, node in tree.filter(javalang.tree.BlockStatement):
                if hasattr(node, 'position') and node.position:
                    block_start_line = node.position.line
                    block_end_line = max([getattr(item, "position", node.position).line 
                                        for item in node.statements]) if hasattr(node, 'statements') and node.statements else node.position.line

                    # Check if block is impacted
                    if any(block_start_line <= line <= block_end_line for line in impacted_lines):
                        # Check if it's a static initializer block
                        is_static = False
                        if hasattr(node, 'modifiers') and node.modifiers:
                            is_static = 'static' in node.modifiers

                        if is_static:
                            impacted_data["impacted_static_blocks"].append(f"static_block_{block_start_line}")
                        else:
                            impacted_data["impacted_instance_blocks"].append(f"instance_block_{block_start_line}")

            # Update the impact level for fields based on references
            impacted_data["impacted_fields"] = {
                field: "high" if data["referenced"] else "low"
                for field, data in field_references.items()
            }

            impacted[file] = impacted_data

        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue

    return impacted


def is_field_referenced(field_name: str, method_body):
    """
    Checks if a field is referenced in a method's body.

    Args:
        field_name (str): The name of the field to search for.
        method_body (list): The body of the method (list of javalang.tree nodes).

    Returns:
        bool: True if the field is referenced, False otherwise.
    """
    if not method_body:
        return False

    for statement in method_body:
        # Handle MockStatement from tests
        if hasattr(statement, 'member') and statement.member == field_name:
            return True

        # Check if the field is used in an Assignment, MemberReference, etc.
        if isinstance(statement, javalang.tree.Assignment):
            # Check left side of assignment
            if isinstance(statement.expressionl, javalang.tree.MemberReference) and statement.expressionl.member == field_name:
                return True
            # Check right side of assignment
            if isinstance(statement.value, javalang.tree.MemberReference) and statement.value.member == field_name:
                return True
        elif isinstance(statement, javalang.tree.MemberReference):
            if statement.member == field_name:
                return True
        elif isinstance(statement, javalang.tree.MethodInvocation):
            # Check if field is used as an argument in method calls
            if hasattr(statement, 'arguments') and statement.arguments:
                for arg in statement.arguments:
                    if isinstance(arg, javalang.tree.MemberReference) and arg.member == field_name:
                        return True
        # Recurse into blocks (e.g., if, for, while, etc.)
        if hasattr(statement, 'children'):
            if is_field_referenced(field_name, statement.children):
                return True
        # Recurse into statement blocks (e.g., if, for, while, etc.)
        if hasattr(statement, 'block') and statement.block:
            if is_field_referenced(field_name, statement.block):
                return True
        # Recurse into then/else statements
        if hasattr(statement, 'then_statement') and statement.then_statement:
            if is_field_referenced(field_name, [statement.then_statement]):
                return True
        if hasattr(statement, 'else_statement') and statement.else_statement:
            if is_field_referenced(field_name, [statement.else_statement]):
                return True
    return False


def extract_impacted_lines(diff_output: str, file_path: str) -> list[int]:
    """
    Extracts line numbers of changes for a specific file from the Git diff output.

    Args:
        diff_output (str): The raw diff output (from `get_git_diff`).
        file_path (str): The file path for which to extract impacted lines.

    Returns:
        list[int]: A list of impacted line numbers.
    """
    impacted_lines = []
    file_diff_found = False
    for line in diff_output.splitlines():
        # Identify the start of diff for the given file
        if line.startswith(f"diff --git a/{file_path} "):
            file_diff_found = True
        elif file_diff_found:
            if line.startswith("@@"):
                # Parse line range from `@@ -old_start,old_length +new_start,new_length @@`
                parts = line.split(" ")
                for part in parts:
                    if part.startswith("+") and "," in part:
                        start_line, line_length = map(int, part[1:].split(","))
                        impacted_lines.extend(range(start_line, start_line + line_length))
            elif line.startswith("diff --git"):
                break
    return impacted_lines
