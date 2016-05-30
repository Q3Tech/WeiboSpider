<template>
    <div>
        <!-- main view -->
        <nav class="navbar navbar navbar-default navbar-fixed-top">
            <div class="navbar-header">
                <a class="navbar-brand" href="#!/">WeiboFollow</a>
            </div>
            <ul class="nav navbar-nav">
                <li><a href="#!/wordfollow/">关键词跟踪</a></li>
                <li><a href="#!/wordfollow-control/">关键词跟踪控制</a></li>
            </ul>
            <div class="navbar-form">
                <input type="text" class="form-control" placeholder="跟踪">
                <button class="btn btn-default">跟踪</button>
            </div>
        </nav>
        <router-view
            class="view"
            keep-alive
            transition
            transition-mode="out-in">
        </router-view>
    </div>
</template>
<style>
    .view {
        padding-top: 50px;
        height:100%;
    }
</style>
