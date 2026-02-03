"""
GraphQL mutation definitions for Shopify Admin API.
Used by the Photo Enhancer system to update product images and tags.
"""

# Create staged upload target for images
STAGED_UPLOADS_CREATE_MUTATION = """
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
    stagedUploadsCreate(input: $input) {
        stagedTargets {
            url
            resourceUrl
            parameters {
                name
                value
            }
        }
        userErrors {
            field
            message
        }
    }
}
"""

# Add media (images) to product
PRODUCT_CREATE_MEDIA_MUTATION = """
mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
    productCreateMedia(productId: $productId, media: $media) {
        media {
            alt
            mediaContentType
            status
            ... on MediaImage {
                id
                image {
                    url
                }
            }
        }
        mediaUserErrors {
            field
            message
        }
    }
}
"""

# Delete media from product
PRODUCT_DELETE_MEDIA_MUTATION = """
mutation productDeleteMedia($productId: ID!, $mediaIds: [ID!]!) {
    productDeleteMedia(productId: $productId, mediaIds: $mediaIds) {
        deletedMediaIds
        mediaUserErrors {
            field
            message
        }
    }
}
"""

# Update product (for tags)
PRODUCT_UPDATE_MUTATION = """
mutation productUpdate($input: ProductInput!) {
    productUpdate(input: $input) {
        product {
            id
            title
            tags
        }
        userErrors {
            field
            message
        }
    }
}
"""

# Files create mutation (for base64 upload)
FILES_CREATE_MUTATION = """
mutation fileCreate($files: [FileCreateInput!]!) {
    fileCreate(files: $files) {
        files {
            id
            alt
            ... on MediaImage {
                image {
                    url
                }
            }
        }
        userErrors {
            field
            message
        }
    }
}
"""
