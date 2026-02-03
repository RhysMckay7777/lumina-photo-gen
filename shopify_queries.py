"""
GraphQL query definitions for Shopify Admin API.
Used by the Photo Enhancer system to fetch products and images.
"""

# Fetch all products with their images (paginated)
PRODUCTS_WITH_IMAGES_QUERY = """
query listProductsWithImages($first: Int!, $after: String) {
    products(first: $first, after: $after) {
        pageInfo {
            hasNextPage
            endCursor
        }
        edges {
            node {
                id
                title
                handle
                status
                tags
                descriptionHtml
                images(first: 20) {
                    edges {
                        node {
                            id
                            url
                            altText
                        }
                    }
                }
            }
        }
    }
}
"""

# Get single product by ID
PRODUCT_BY_ID_QUERY = """
query getProduct($id: ID!) {
    product(id: $id) {
        id
        title
        handle
        status
        tags
        descriptionHtml
        images(first: 20) {
            edges {
                node {
                    id
                    url
                    altText
                }
            }
        }
    }
}
"""

# Get shop info for validation
SHOP_INFO_QUERY = """
query {
    shop {
        id
        name
        email
        primaryDomain {
            url
            host
        }
        currencyCode
    }
}
"""

# Count products
PRODUCTS_COUNT_QUERY = """
query {
    productsCount {
        count
    }
}
"""
