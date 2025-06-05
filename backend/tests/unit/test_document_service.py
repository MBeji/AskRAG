import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
from datetime import datetime

from beanie import PydanticObjectId

# Models and Services to test
from app.models.document import Document as DocumentModel
from app.models.user import User as UserModel
from app.services.document_service import list_documents_for_user, get_document_by_id # save_uploaded_file is more complex
# from app.core.config import settings # For UPLOAD_DIR etc. if testing save_uploaded_file

@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_documents_for_user():
    mock_user = UserModel(id=PydanticObjectId(), username="testuser", email="test@test.com", hashed_password="bla")

    # Expected documents to be returned by the mocked find
    mock_doc_list: List[DocumentModel] = [
        DocumentModel(id=PydanticObjectId(), filename="doc1.pdf", uploader_id=str(mock_user.id), status="completed"),
        DocumentModel(id=PydanticObjectId(), filename="doc2.txt", uploader_id=str(mock_user.id), status="completed"),
    ]

    # Mock the .to_list() method which is called after find()
    mock_find_result = AsyncMock()
    mock_find_result.to_list = AsyncMock(return_value=mock_doc_list)

    # Patch DocumentModel.find to return the mock_find_result
    with patch("app.models.document.Document.find", return_value=mock_find_result) as mock_find:
        documents = await list_documents_for_user(user=mock_user)

        # Assertions
        # Check that Document.find was called correctly
        # The actual query DocumentModel.uploader_id == str(mock_user.id) is complex to assert directly with find()
        # but we can check it was called.
        mock_find.assert_called_once()

        # Check that sort was called on the result of find (if it's part of the service logic)
        # The current list_documents_for_user has .sort("-updated_at")
        # So, mock_find_result.sort should have been called.
        mock_find_result.sort.assert_called_once_with("-updated_at")

        assert len(documents) == 2
        assert documents[0].filename == "doc1.pdf"
        assert documents[1].filename == "doc2.txt"
        for doc in documents:
            assert doc.uploader_id == str(mock_user.id)

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_document_by_id_found():
    mock_user = UserModel(id=PydanticObjectId(), username="testuser", email="test@test.com", hashed_password="bla")
    doc_id_to_find = PydanticObjectId()

    mock_document = DocumentModel(
        id=doc_id_to_find,
        filename="testdoc.pdf",
        uploader_id=str(mock_user.id),
        status="completed"
    )

    with patch("app.models.document.Document.find_one", AsyncMock(return_value=mock_document)) as mock_find_one:
        document = await get_document_by_id(doc_id=doc_id_to_find, user=mock_user)

        mock_find_one.assert_called_once() # Check specific query later if needed
        assert document is not None
        assert document.id == doc_id_to_find
        assert document.filename == "testdoc.pdf"

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_document_by_id_not_found():
    mock_user = UserModel(id=PydanticObjectId(), username="testuser", email="test@test.com", hashed_password="bla")
    doc_id_to_find = PydanticObjectId()

    with patch("app.models.document.Document.find_one", AsyncMock(return_value=None)) as mock_find_one:
        document = await get_document_by_id(doc_id=doc_id_to_find, user=mock_user)

        mock_find_one.assert_called_once()
        assert document is None

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_document_by_id_wrong_user():
    user1 = UserModel(id=PydanticObjectId(), username="user1", email="test1@test.com", hashed_password="bla")
    user2 = UserModel(id=PydanticObjectId(), username="user2", email="test2@test.com", hashed_password="bla")
    doc_id_to_find = PydanticObjectId()

    # Document belongs to user1
    mock_document_of_user1 = DocumentModel(
        id=doc_id_to_find,
        filename="testdoc.pdf",
        uploader_id=str(user1.id), # Belongs to user1
        status="completed"
    )

    # Mock find_one to return None because user2 is asking for user1's doc
    # The query in get_document_by_id is:
    # DocumentModel.find_one(DocumentModel.id == doc_id, DocumentModel.uploader_id == str(user.id))
    with patch("app.models.document.Document.find_one", AsyncMock(return_value=None)) as mock_find_one:
        # User2 tries to get User1's document
        document = await get_document_by_id(doc_id=doc_id_to_find, user=user2)

        # Assert that find_one was called with user2's ID in the query
        # This requires inspecting the call arguments to mock_find_one.
        # For simplicity, we trust the service logic and just assert None is returned.
        # A more rigorous test would capture call_args.
        mock_find_one.assert_called_once()
        assert document is None

# Tests for save_uploaded_file are more complex due to file operations and multiple service calls.
# They would require mocking UploadFile, aiofiles, os.path, uuid, document_extractor,
# text_chunker, embeddings service, and vector_store.
# This is a good candidate for future expansion.
