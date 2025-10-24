// Common Excel preview function
function setupExcelUpload(prefix) {
  const fileInput = document.getElementById(`file-input-${prefix}`);
  const chooseBtn = document.getElementById(`choose-btn-${prefix}`);
  const dropZone = document.getElementById(`drop-zone-${prefix}`);
  const fileNameDisplay = document.getElementById(`file-name-${prefix}`);
  const previewDiv = document.getElementById(`preview-${prefix}`);

  // Open file dialog
  chooseBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', handleFiles);

  // Drag & drop
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#0078d7";
    dropZone.style.background = "#f0f8ff";
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = "#cbd5e0";
    dropZone.style.background = "white";
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#cbd5e0";
    dropZone.style.background = "white";
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      handleFiles();
    }
  });

  // Handle file selection
  function handleFiles() {
    const file = fileInput.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'xlsx') {
      alert('Invalid file type! Please upload only .xlsx files.');
      fileInput.value = '';
      fileNameDisplay.textContent = '';
      previewDiv.innerHTML = '';
      return;
    }

    fileNameDisplay.textContent = `📄 Selected file: ${file.name}`;
    previewDiv.innerHTML = '<em>Loading preview...</em>';

    const reader = new FileReader();
    reader.onload = function(e) {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(sheet, { header: 1 });
      displayPreview(json);
    };
    reader.readAsArrayBuffer(file);
  }

  // Display the preview table
  function displayPreview(data) {
    if (!data.length) {
      previewDiv.innerHTML = "<p>No data found in the file.</p>";
      return;
    }

    let html = "<table><thead><tr>";
    data[0].forEach(col => html += `<th>${col}</th>`);
    html += "</tr></thead><tbody>";

    const previewRows = data.slice(1, 8); // Show first 7 rows
    previewRows.forEach(row => {
      html += "<tr>";
      row.forEach(cell => html += `<td>${cell ?? ""}</td>`);
      html += "</tr>";
    });

    html += "</tbody></table>";
    previewDiv.innerHTML = html;
  }
}

// Setup both uploads
setupExcelUpload("train");
setupExcelUpload("test");

// Function to create and show the popup
function showSuccessPopup(downloadUrl) {
  // Create modal container
  const modal = document.createElement('div');
  modal.style.position = 'fixed';
  modal.style.top = '0';
  modal.style.left = '0';
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
  modal.style.display = 'flex';
  modal.style.justifyContent = 'center';
  modal.style.alignItems = 'center';
  modal.style.zIndex = '1000';

  // Create modal content
  const modalContent = document.createElement('div');
  modalContent.style.backgroundColor = '#fff';
  modalContent.style.padding = '20px';
  modalContent.style.borderRadius = '8px';
  modalContent.style.textAlign = 'center';
  modalContent.style.maxWidth = '400px';
  modalContent.style.width = '90%';

  // Add message
  const message = document.createElement('p');
  message.textContent = 'Calculation completed successfully!';
  message.style.marginBottom = '20px';
  modalContent.appendChild(message);

  // Create button container
  const buttonContainer = document.createElement('div');
  buttonContainer.style.display = 'flex';
  buttonContainer.style.justifyContent = 'center';
  buttonContainer.style.gap = '10px';

  // Create OK button
  const okButton = document.createElement('button');
  okButton.textContent = 'OK';
  okButton.style.padding = '10px 20px';
  okButton.style.background = 'linear-gradient(135deg, #0078d7, #20c284)';
  okButton.style.color = '#fff';
  okButton.style.border = 'none';
  okButton.style.borderRadius = '8px';
  okButton.style.cursor = 'pointer';
  okButton.addEventListener('click', () => {
    document.body.removeChild(modal);
    window.URL.revokeObjectURL(downloadUrl); // Revoke URL when closing modal
  });

  // Create Export button
  const exportButton = document.createElement('button');
  exportButton.textContent = 'Export';
  exportButton.style.padding = '10px 20px';
  exportButton.style.background = 'linear-gradient(135deg, #20c284, #0078d7)';
  exportButton.style.color = '#fff';
  exportButton.style.border = 'none';
  exportButton.style.borderRadius = '8px';
  exportButton.style.cursor = 'pointer';
  exportButton.addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = 'rasar_descriptors_output.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
    document.body.removeChild(modal);
    window.URL.revokeObjectURL(downloadUrl); // Revoke URL after download
  });

  // Append buttons to container
  buttonContainer.appendChild(okButton);
  buttonContainer.appendChild(exportButton);
  modalContent.appendChild(buttonContainer);

  // Append content to modal
  modal.appendChild(modalContent);

  // Append modal to body
  document.body.appendChild(modal);
}

// Handle submit button click
const submitBtn = document.getElementById('final_submit');
submitBtn.addEventListener('click', async () => {
  const trainFileInput = document.getElementById('file-input-train');
  const testFileInput = document.getElementById('file-input-test');
  const methodSelect = document.querySelector('select');
  const descriptorType = methodSelect.value;

  if (!trainFileInput.files[0] || !testFileInput.files[0]) {
    alert('Please upload both training and test files.');
    return;
  }

  const formData = new FormData();
  formData.append('train_file', trainFileInput.files[0]);
  formData.append('test_file', testFileInput.files[0]);
  formData.append('method', 'Gaussian Kernel'); // Default, can be made dynamic
  formData.append('descriptor_type', descriptorType);

  submitBtn.textContent = 'Processing...';
  submitBtn.disabled = true;

  try {
    const response = await fetch('https://rasar-calculator-5.onrender.com', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Calculation failed');
    }

    // Handle file download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    showSuccessPopup(url); // Show popup with valid URL
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    submitBtn.textContent = '🚀 Submit';
    submitBtn.disabled = false;
  }
});
