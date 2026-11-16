import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "wavespeed_connect_api.WaveSpeedReferenceToVideo",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "WaveSpeedReferenceToVideo") {
            // Store the original onExecuted method if it exists
            const onExecuted = nodeType.prototype.onExecuted;
            
            nodeType.prototype.onExecuted = function(message) {
                // Call the original onExecuted if it exists
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }
                
                // Handle the UI data from the backend
                if (message && message.text) {
                    this.showText = message.text;
                    // Trigger a redraw
                    this.setDirtyCanvas(true, true);
                }
                
                if (message && message.video_url) {
                    this.videoUrl = message.video_url[0] || "";
                }
                
                if (message && message.task_id) {
                    this.taskId = message.task_id[0] || "";
                }
            };
            
            // Override the draw method to display text on the node
            const onDrawForeground = nodeType.prototype.onDrawForeground;
            nodeType.prototype.onDrawForeground = function(ctx) {
                // Call the original draw method
                if (onDrawForeground) {
                    onDrawForeground.apply(this, arguments);
                }
                
                // Display the text if available
                if (this.showText && this.showText.length > 0) {
                    const text = Array.isArray(this.showText) ? this.showText.join("\n") : this.showText;
                    
                    // Set up text styling
                    ctx.save();
                    ctx.font = "12px Arial";
                    ctx.fillStyle = "#ffffff";
                    ctx.textAlign = "left";
                    
                    // Calculate position (below the node's normal content)
                    const lines = text.split("\n");
                    const lineHeight = 16;
                    const padding = 10;
                    const startY = this.size[1] + padding;
                    
                    // Draw background for text area
                    const textHeight = lines.length * lineHeight + padding * 2;
                    const maxWidth = Math.max(this.size[0], 300);
                    
                    ctx.fillStyle = "#1a1a1a";
                    ctx.fillRect(0, startY, maxWidth, textHeight);
                    
                    // Draw border
                    ctx.strokeStyle = "#4a4a4a";
                    ctx.lineWidth = 1;
                    ctx.strokeRect(0, startY, maxWidth, textHeight);
                    
                    // Draw text
                    ctx.fillStyle = "#ffffff";
                    let y = startY + padding + lineHeight;
                    
                    for (const line of lines) {
                        // Truncate long lines
                        let displayLine = line;
                        if (line.length > 80) {
                            displayLine = line.substring(0, 77) + "...";
                        }
                        ctx.fillText(displayLine, padding, y);
                        y += lineHeight;
                    }
                    
                    // Update node size to accommodate the text
                    const newHeight = startY + textHeight + padding;
                    if (newHeight > this.size[1]) {
                        this.size[1] = newHeight;
                    }
                    if (maxWidth > this.size[0]) {
                        this.size[0] = maxWidth;
                    }
                    
                    ctx.restore();
                }
                
                // Display video URL if available
                if (this.videoUrl) {
                    ctx.save();
                    ctx.font = "10px Arial";
                    ctx.fillStyle = "#00ff00";
                    ctx.textAlign = "left";
                    
                    const urlText = `Video URL: ${this.videoUrl.substring(0, 50)}${this.videoUrl.length > 50 ? '...' : ''}`;
                    ctx.fillText(urlText, 10, this.size[1] - 20);
                    
                    ctx.restore();
                }
                
                // Display task ID if available
                if (this.taskId) {
                    ctx.save();
                    ctx.font = "10px Arial";
                    ctx.fillStyle = "#00ffff";
                    ctx.textAlign = "left";
                    
                    const taskText = `Task ID: ${this.taskId}`;
                    ctx.fillText(taskText, 10, this.size[1] - 5);
                    
                    ctx.restore();
                }
            };
        }
    }
});
