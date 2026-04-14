# LM2Ollama - LM Studio to Ollama Model Linker

A Python application that bridges LM Studio models with Ollama by creating symbolic links, allowing you to use LM Studio models in Ollama without duplicating storage space.

## Features

- **Space Efficient**: Creates symbolic links instead of copying files
- **Automated Naming**: Smart model naming based on GGUF file names
- **Progress Tracking**: Real-time progress updates and logs
- **Error Handling**: Comprehensive error reporting with user-friendly messages
- **Cross-Platform Compatible**: Works with Windows systems

## How It Works

1. Select an LM Studio model folder containing a `.gguf` file
2. The application creates a Modelfile from the GGUF file
3. Uses Ollama's `create` command to register the model
4. Creates symbolic links to reclaim disk space
5. Shows progress and completion status

## Prerequisites

- Python 3.7 or higher
- LM Studio installed with models
- Ollama installed and running
- Administrative privileges (required for creating symlinks)

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install tkinter
   ```
3. Ensure LM Studio and Ollama are properly installed and configured

## Usage

1. Run the application:
   ```bash
   python LM2Ollama.py
   ```

2. Click the "[ SELECT MODEL FOLDER ]" button to choose an LM Studio model folder

3. The application will:
   - Identify the largest GGUF file in the selected folder
   - Create a Modelfile with the correct path
   - Register the model with Ollama
   - Create symbolic links to reclaim space
   - Display progress and completion status

## UI Improvements Suggested

### Current Issues:
- Limited visual feedback during operations
- Basic progress indication
- Minimal error handling visualization
- Monochromatic color scheme
- No loading states or animations

### Proposed Improvements:
1. **Enhanced Visual Design**:
   - Modern color scheme with better contrast
   - Improved button styling and hover effects
   - More intuitive layout organization

2. **Better User Feedback**:
   - Progress indicators for each step
   - Clearer status messages
   - Visual warnings for potential issues
   - Loading animations during operations

3. **Improved Functionality**:
   - Model preview before linking
   - Batch processing capability
   - History of linked models
   - Settings panel for customization

4. **Accessibility Features**:
   - Better keyboard navigation
   - High contrast mode options
   - Screen reader support

## Troubleshooting

### Common Issues:

1. **Permission Error**: 
   - Run as administrator when creating symlinks
   - Ensure Ollama is running with proper permissions

2. **Model Not Found**:
   - Verify the folder contains a `.gguf` file
   - Check that LM Studio models are properly installed

3. **Space Reclamation Issues**:
   - Make sure Ollama's blob directory exists
   - Confirm sufficient disk space for operations

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, please open an issue in the repository or contact the maintainer.