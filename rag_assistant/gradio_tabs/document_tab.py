import gradio as gr


class DocumentTab(gr.Interface):
    def __init__(self, assistant, show_documents_tab, _init_file_path=None):
        self.assistant = assistant
        self.show_documents_tab = show_documents_tab
        self._init_file_path = _init_file_path

        self.documents = []

    # ------------------------------ Tab ------------------------------
    def document_tab(self):
        with gr.Blocks(css=self.assistant.css) as self.document_table:
            self._doc_upload()
            self._doc_table()
            self._document_event_handler()

    # -------------------------------------------------- COMPONENTS ------------------------------------------------------
    def _doc_upload(self):
        with gr.Row():
            self.file = gr.File(
                label="Upload JSON/PDF/txt File",
                value=self._init_file_path,
                file_count="multiple",
                file_types=[".json", ".pdf", ".txt"],
            )
        self.vector_store = gr.Dropdown(
            choices=self.assistant.available_vector_stores.keys(),
            value=list(self.assistant.available_vector_stores.keys())[0],
            label="Select vector_store",
        )
        self.load_button = gr.Button("load")
        # Place event handlers inside the Blocks context
        self.vector_store.change(
            self.assistant.set_vector_store,
            inputs=[self.vector_store],
            outputs=[],
        )

    def _doc_table(self):
        with gr.Row():
            if self._init_file_path:
                df = self.assistant._load_and_filter_json(self._init_file_path)
            self.data_frame = gr.Dataframe(
                headers=["Document", "Status", "Timestamp"],
                col_count=(3, "fixed"),
                interactive=True,
                wrap=True,
                line_breaks=True,
                elem_id="document-table-container",
                # height="700",
                # value=df,
            )

    # -------------------------------------------------- HANDLERS ------------------------------------------------------
    def _on_load_document(self, files):
        """Loads a document and updates the document table."""
        if files is None:
            return None, gr.update(value="")

        for file in files:
            file_type = file.name.split(".")[-1]
            doc_name = file.name
            if file_type == "json":
                self.assistant.load_json_from_file_info(file)
            elif file_type == "pdf":
                self.assistant.load_pdf_from_file_info(file)
            from datetime import datetime

            # Create a new row as a list (expected format by gr.Dataframe)
            new_row = [
                doc_name,
                "Loaded",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
            self.documents.append(new_row)

            # Safely extract the current data or initialize an empty list
            current_data = self.data_frame.value

            # Ensure the data is a list of lists
            current_data["data"] = self.documents

            self.data_frame.value = current_data

            # Clear the file input and return the updated dataframe
            return None, gr.update(value=current_data)

        # If no file is provided, return the current state
        return None, self.documents

    def _document_event_handler(self):
        """Set up the load button click event."""
        self.load_button.click(
            fn=self._on_load_document,
            inputs=[self.file],  # Input: Uploaded file
            outputs=[
                self.file,
                self.data_frame,
            ],  # Output: Clear file input, update dataframe
        )