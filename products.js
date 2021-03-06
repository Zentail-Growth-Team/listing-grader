let ok = "https://assets.website-files.com/5d60672844a280322e776b37/5d856c118de89c48f98b29a8_icons8-ok.svg";
let ex = "https://assets.website-files.com/5d60672844a280322e776b37/5d856c7e9d773336f7b25fc3_icons8-box-important%20(1).svg";
let product_table = document.getElementById("product-table");
let pr = document.getElementById("Table-row");
let pr_ex = document.getElementById("Table-row-expand");
let num_of_products = 0;
function expand_product(id) {
    let row_to_exp = document.getElementById("Table-row-expand-" + id.replace("Table-row-", ""));
    let expand_sign = document.getElementById(id).getElementsByClassName('vertical')[0];
    if (row_to_exp.getAttribute("style").includes("height: 0px;") === true){
        row_to_exp.setAttribute("style",
            row_to_exp.getAttribute("style").replace("height: 0px;", ""));
        expand_sign.setAttribute('hidden', 'true');
    }
    else if (row_to_exp.getAttribute("style").includes("height: 0px;") === false){
        row_to_exp.setAttribute("style",
            row_to_exp.getAttribute("style") + " height: 0px;");
        expand_sign.removeAttribute('hidden');
    }
}
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
json = json.replace(/\u00a0/g, ' ');
json = json.replace(/&#39;/g,"'");
json = json.replace(/&amp;/g,"&");
JSON.parse(json.replace(/&quot;/g,'"')).forEach(function(product) {
    num_of_products = num_of_products + 1;
    pr.id = "Table-row-" + num_of_products;
    pr_ex.id = "Table-row-expand-" + num_of_products;
    pr_ex.setAttribute("style", "height: 0px;");
    let link = pr_ex.getElementsByClassName("link-to-amazon")[0];
    link.setAttribute("href", "https://www.amazon.com/dp/" + product.product);
    pr.onclick = function (){expand_product(this.id)};
    let title = (pr.getElementsByClassName("second")[0]).getElementsByClassName("tittle-heading-4")[0];
    title.innerText = product.title.replace(/\[replace-quote\]/g, "\"").replace(/\[replace-single\]/g, "\'");
    let reviews = (pr.getElementsByClassName("fourth")[0]).getElementsByClassName("tittle-heading-4")[0];
    reviews.innerText = numberWithCommas(product.num_reviews) + " Customer Reviews";
    let copy_score = Math.round((product.title_score*.425) + (product.description_score*.425) + (product.bullets_score));
    let total_score = Math.round((copy_score + product.media_score + product.ratings_reviews_score)/3);
    let score_block = pr.getElementsByClassName("score-block")[0];
    let score_block_number = score_block.getElementsByClassName("number")[0];
    let score_color = "#F70D49";
    if (total_score >= 90){
        score_color = "#4BD2E1";
    }
    else if (total_score >= 80){
        score_color = "#428AE7";
    }
    else if (total_score >= 70){
        score_color = "#FDBE38";
    }
    else if (total_score >= 60){
        score_color = "#ED8919";
    }
    score_block.setAttribute("style", "background-color:" + score_color + ";");
    score_block_number.innerText = total_score + "%";
    let pid = pr.getElementsByClassName("image-div")[0];
    if (product.feature_image_url == null){
        pid.setAttribute("style", "background-image: url('')")
    }
    else{
        pid.setAttribute("style", "background-image: url('" + product.feature_image_url +"')")
    }
    let si = (pr.getElementsByClassName("third")[0]).getElementsByClassName("star-icon");
    if (product.rating < 1){
        si[0].classList.add("gray");
        si[1].classList.add("gray");
        si[2].classList.add("gray");
        si[3].classList.add("gray");
        si[4].classList.add("gray");
    }
    else if (product.rating < 1.5){
        si[0].classList.remove("gray");
        si[1].classList.add("gray");
        si[2].classList.add("gray");
        si[3].classList.add("gray");
        si[4].classList.add("gray");
    }
    else if (product.rating < 2.5){
        si[0].classList.remove("gray");
        si[1].classList.remove("gray");
        si[2].classList.add("gray");
        si[3].classList.add("gray");
        si[4].classList.add("gray");
    }
    else if (product.rating < 3.5){
        si[0].classList.remove("gray");
        si[1].classList.remove("gray");
        si[2].classList.remove("gray");
        si[3].classList.add("gray");
        si[4].classList.add("gray");
    }
    else if (product.rating < 4.5){
        si[0].classList.remove("gray");
        si[1].classList.remove("gray");
        si[2].classList.remove("gray");
        si[3].classList.remove("gray");
        si[4].classList.add("gray");
    }
    else {
        si[0].classList.remove("gray");
        si[1].classList.remove("gray");
        si[2].classList.remove("gray");
        si[3].classList.remove("gray");
        si[4].classList.remove("gray");
    }

    let scores = pr_ex.getElementsByTagName("span");
    let copy_color = "#F70D49";
    let media_color = "#F70D49";
    let reviews_color = "#F70D49";
    if (copy_score >= 90){
        copy_color = "#4BD2E1";
    }
    else if (copy_score >= 80){
        copy_color = "#428AE7";
    }
    else if (copy_score >= 70){
        copy_color = "#FDBE38";
    }
    else if (copy_score >= 60){
        copy_color = "#ED8919";
    }
    if (product.media_score >= 90){
        media_color = "#4BD2E1";
    }
    else if (product.media_score >= 80){
        media_color = "#428AE7";
    }
    else if (product.media_score >= 70){
        media_color = "#FDBE38";
    }
    else if (product.media_score >= 60){
        media_color = "#ED8919";
    }
    if (product.ratings_reviews_score >= 90){
        reviews_color = "#4BD2E1";
    }
    else if (product.ratings_reviews_score >= 80){
        reviews_color = "#428AE7";
    }
    else if (product.ratings_reviews_score >= 70){
        reviews_color = "#FDBE38";
    }
    else if (product.ratings_reviews_score >= 60){
        reviews_color = "#ED8919";
    }
    scores[0].innerHTML = "<strong id=\"copy-score\" style=\"color:" + copy_color + "\">" + copy_score + "/100</strong>";
    scores[1].innerHTML = "<strong id=\"media-score\" style=\"color:" + media_color + "\">" + product.media_score + "/100</strong>";
    scores[2].innerHTML = "<strong id=\"reviews-score\" style=\"color:" + reviews_color + "\">" + product.ratings_reviews_score + "/100</strong>";

    let checks = pr_ex.getElementsByTagName("img");
    if (product.title_num_all_caps === 0) {
        checks[0].src = ok
    }
    else {
        checks[0].src = ex
    }
    if ((product.title_character_count >= 80) && (product.title_character_count <= 120)) {
        checks[2].src = ok
    }
    else {
        checks[2].src = ex
    }
    if (product.title_num_lower_case === 0) {
        checks[3].src = ok
    }
    else {
        checks[3].src = ex
    }
    if (product.title_num_incorrect_caps === 0) {
        checks[4].src = ok
    }
    else {
        checks[4].src = ex
    }
    if (product.title_contains_seo_adverse_chars === false) {
        checks[5].src = ok
    }
    else {
        checks[5].src = ex
    }
    if (product.title_contains_ascii === false) {
        checks[6].src = ok
    }
    else {
        checks[6].src = ex
    }
    if (product.title_contains_promo_phrase === false) {
        checks[7].src = ok
    }
    else {
        checks[7].src = ex
    }
    if (product.description_num_lower_case_bullets === 0) {
        checks[8].src = ok
    }
    else {
        checks[8].src = ex
    }
    if (product.description_num_bullets >= 5) {
        checks[9].src = ok
    }
    else {
        checks[9].src = ex
    }
    if (product.description_contains_html === false) {
        checks[10].src = ok
    }
    else {
        checks[10].src = ex
    }
    if (product.description_character_count >= 250) {
        checks[11].src = ok
    }
    else {
        checks[11].src = ex
    }
    if (product.description_contains_quotes === false) {
        checks[12].src = ok
    }
    else {
        checks[12].src = ex
    }
    if (product.description_contains_price_condition_info === false) {
        checks[13].src = ok
    }
    else {
        checks[13].src = ex
    }
    if (product.description_contains_shipping_info === false) {
        checks[14].src = ok
    }
    else {
        checks[14].src = ex
    }
    if (product.description_contains_contact_info === false) {
        checks[15].src = ok
    }
    else {
        checks[15].src = ex
    }
    if (product.extra_content_score === 0) {
        checks[16].src = ex
    }
    else {
        checks[16].src = ok
    }
    if (product.media_low_qual_images === 0) {
        checks[17].src = ok
    }
    else {
        checks[17].src = ex
    }
    if (product.media_num_images >= 5) {
        checks[18].src = ok
    }
    else {
        checks[18].src = ex
    }
    if (product.media_num_videos >= 1) {
        checks[19].src = ok
    }
    else {
        checks[19].src = ex
    }
    if (product.rating >= 4) {
        checks[20].src = ok
    }
    else {
        checks[20].src = ex
    }
    if (product.num_reviews >= 20) {
        checks[21].src = ok
    }
    else {
        checks[21].src = ex
    }
    let fill_ins = pr_ex.getElementsByClassName("fill-in");
    fill_ins[0].innerText = "Your character count is " + product.title_character_count;
    fill_ins[1].innerText = "Your listing has " + product.description_num_bullets + " bullet point(s)";
    fill_ins[2].innerText = "Your character count is " + product.description_character_count;
    fill_ins[3].innerText = "Your image count is " + product.media_num_images;
    fill_ins[4].innerText = "Your video count is " + product.media_num_videos;
    fill_ins[5].innerText = "The average rating is " + product.rating + " stars";
    fill_ins[6].innerText = "Your product has " + numberWithCommas(product.num_reviews) + " review(s)";
    if(num_of_products !== 1){
        product_table.appendChild(pr);
        product_table.appendChild(pr_ex);
    }
    pr = pr.cloneNode(true);
    pr_ex = pr_ex.cloneNode(true);
});
if(num_of_products !== 0){
    document.getElementById("Table-Row-Sec").removeAttribute("hidden");
}