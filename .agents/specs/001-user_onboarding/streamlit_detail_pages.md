Excellent question. This is a very common and sophisticated use case: you want a page that is only accessible *contextually* (by clicking on an item) and not through general navigation.

Yes, you can absolutely achieve this. The solution involves two key Streamlit features:

1.  A special naming convention to **hide a page** from the sidebar.
2.  Using `st.query_params` to **pass the item's ID** in the URL.

Here is the complete guide and code to set it up.

---

### Step 1: Hide the Detail Page from Navigation

Streamlit has a built-in rule for this: **Any page file in the `pages/` directory that starts with an underscore (`_`) or a dot (`.`) will not be shown in the navigation sidebar.**

So, your file structure should look like this. Notice the underscore in front of the detail page's filename.

```
your_project_folder/
├── Home.py                     # Your main script, the "Index Page"
└── pages/
    ├── _Item_Details.py        # The HIDDEN "Detail Page"
    └── 1_Another_Visible_Page.py # A regular page that WILL show up
```

With this structure, when you run your app, the sidebar will only show "Home" and "Another Visible Page". "Item Details" will be completely hidden from the navigation list.

### Step 2: Use Query Params to Link Pages

Now we need to link the `Home.py` page to the hidden `_Item_Details.py` page using a URL that contains the specific item ID.

#### On the Index Page (`Home.py`)

You will use `st.markdown()` to create hyperlinks. The URL will point to the detail page and include a query parameter like `?item_id=some_value`.

Streamlit automatically creates a URL path from the filename. It will strip the leading underscore and the `.py` extension. So, `pages/_Item_Details.py` becomes accessible at the path `/Item_Details`.

**`Home.py`**
```python
import streamlit as st

# Function to simulate fetching data (keep this consistent across pages)
def get_data():
    return {
        "item1": {"name": "Streamlit Super-Widget", "description": "The best widget for all your app needs.", "price": 99.99},
        "item2": {"name": "DataCruncher Pro", "description": "Process data at lightning speed.", "price": 149.50},
        "item3": {"name": "CloudVisualizer 3D", "description": "Visualize your cloud infrastructure in 3D.", "price": 299.00},
    }

st.set_page_config(
    page_title="Our Product Catalog",
    layout="wide"
)

st.title("Product Catalog")
st.write("Click on any product to see more details.")

items = get_data()

# Display each item with a markdown link
for item_id, item_info in items.items():
    st.subheader(item_info['name'])
    st.write(item_info['description'])
    
    # This is the key part!
    # We create a markdown link to the details page, passing the item_id in the URL.
    # The URL path is the filename without the underscore and extension.
    link = f"/[Item_Details?item_id={item_id}]({item_info['name']})"
    st.markdown(f"**➡️ [View Details for {item_info['name']}](Item_Details?item_id={item_id})**")
    st.divider()
```

#### On the Detail Page (`pages/_Item_Details.py`)

This page's job is to read the `item_id` from the URL, fetch the corresponding data, and display it. If no `item_id` is found, it should show a helpful message.

**`pages/_Item_Details.py`**
```python
import streamlit as st

# Use the same data-fetching function
def get_data():
    return {
        "item1": {"name": "Streamlit Super-Widget", "description": "The best widget for all your app needs.", "price": 99.99},
        "item2": {"name": "DataCruncher Pro", "description": "Process data at lightning speed.", "price": 149.50},
        "item3": {"name": "CloudVisualizer 3D", "description": "Visualize your cloud infrastructure in 3D.", "price": 299.00},
    }

st.set_page_config(page_title="Product Details")

# st.query_params is a dictionary-like object.
# We use .get() to safely access the item_id. It returns None if the key doesn't exist.
try:
    item_id = st.query_params["item_id"]
except KeyError:
    st.error("No item selected. Please go back to the home page and select an item.")
    st.page_link("Home.py", label="Go back to Home", icon="🏠")
    st.stop()


# Now that we have the item_id, fetch all data and find the specific item
all_items = get_data()
item_info = all_items.get(item_id)

# Display the item details if found
if item_info:
    st.title(item_info['name'])
    st.subheader("Product Details")
    st.write(f"**Description:** {item_info['description']}")
    st.metric(label="Price", value=f"${item_info['price']:.2f}")
    
    # You can add more details, images, etc. here
    st.image("https://static.streamlit.io/examples/cat.jpg", caption=f"An image of the {item_info['name']}")

else:
    st.error("Item not found. The selected item ID is invalid.")

# Always provide a way to go back
st.page_link("Home.py", label="Back to Catalog", icon="⬅️")

```
*Note: The code above uses a `try-except` block which is a very robust way to handle the missing query parameter.*

### How It Works and Why It's a Great Pattern

1.  **Run the App:** Start your app with `streamlit run Home.py`.
2.  **Index Page View:** You will see your product catalog. The sidebar will *not* have an "Item Details" link.
3.  **User Clicks a Link:** A user clicks on "View Details for Streamlit Super-Widget".
4.  **URL Change:** Their browser navigates to a URL that looks like `http://localhost:8501/Item_Details?item_id=item1`.
5.  **Detail Page Renders:** Streamlit loads and runs the `pages/_Item_Details.py` script.
6.  **Data is Fetched:** The script reads `item1` from the URL using `st.query_params`, looks it up in your data, and displays the full details.

This approach gives you the best of both worlds:
*   **Clean Navigation:** Your sidebar isn't cluttered with pages that shouldn't be accessed directly.
*   **Bookmarkable URLs:** Users can bookmark or share the link to a specific product's detail page, and it will work perfectly.
*   **Logical User Flow:** It enforces the intended "index -> detail" workflow.