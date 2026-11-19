import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "wavespeed.wavespeedreftovideo.update_status",
    async setup(){
        function messageHandler(event){
            // console.log(event.detail.message)
            for(const node of app.graph._nodes){
                // console.log(node.comfyClass)
                if(node.comfyClass == "WaveSpeedSeeddanceRefToVideo") {
                    for(let i = 0; i < node.widgets.length; i++){
                        // console.log(node.widgets[i])
                        if(node.widgets[i].name == "Status"){
                            node.widgets[i].value = event.detail.message
                        }
                    }
                }
            }
        }
        app.api.addEventListener("wavespeed.wavespeedreftovideo.update_status", messageHandler);
    },

    async nodeCreated(node){
        // console.log(node)
        if (node.comfyClass == "WaveSpeedSeeddanceRefToVideo") {
            // console.log("loading wavespeedreftovideo")
            node.addWidget("text", "Status", "", function(v){
                console.log('new value is ' + v)
            })
            node.serialize_widgets = true
        }
    }
    
});
