function ajax(method, url, data, on_success){

    var formData = new FormData();
    for(var key in data){
        formData.append(key, data[key]);
    }

    var xhr = new XMLHttpRequest();
    xhr.open(method, url);
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200){
            var response = JSON.parse(xhr.response)
            if(response.status == "error"){
                alert(response.msg)
            }else{
                on_success(response)
            }
        }
    }
    
    xhr.send(formData);
}