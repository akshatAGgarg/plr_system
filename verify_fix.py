from common.models import Node
from generator.robula import RobulaPlus

def test_class_uniqueness():
    print("Testing RobulaPlus Class Uniqueness Fix...")
    
    # Create a tree where 'link-text-2' is unique
    new_root = Node(tag="body", children=[
        Node(tag="div", attributes={"class": "navbar"}, children=[
            Node(tag="div", attributes={"class": "link-text-2"}, text="Login")
        ]),
        Node(tag="div", attributes={"class": "footer"}, text="Copyright")
    ])
    
    target_node = new_root.children[0].children[0]
    
    robula = RobulaPlus()
    xpath = robula.generate_xpath(target_node, new_root)
    
    print(f"Generated XPath: {xpath}")
    
    expected = "//div[contains(@class, 'link-text-2')]"
    if xpath == expected:
        print("SUCCESS: Unique class correctly identified.")
    else:
        print(f"FAILURE: Expected {expected}, but got {xpath}")

    # Create a tree where 'link-text-2' is NOT unique
    non_unique_root = Node(tag="body", children=[
        Node(tag="div", attributes={"class": "link-text-2"}, text="Link 1"),
        Node(tag="div", attributes={"class": "link-text-2"}, text="Link 2")
    ])
    
    target_node_2 = non_unique_root.children[0]
    xpath_2 = robula.generate_xpath(target_node_2, non_unique_root)
    
    print(f"Generated XPath (Non-Unique): {xpath_2}")
    
    if "contains" not in xpath_2:
        print("SUCCESS: System correctly fell back to positional/tag XPath when class was not unique.")
    else:
        print("FAILURE: System used a non-unique class.")

if __name__ == "__main__":
    test_class_uniqueness()
